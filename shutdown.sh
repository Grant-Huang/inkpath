#!/bin/bash
# 墨径系统优雅关闭脚本

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PID_DIR="$PROJECT_ROOT/.pids"
FLASK_PID_FILE="$PID_DIR/flask.pid"
NEXTJS_PID_FILE="$PID_DIR/nextjs.pid"
WORKER_PID_FILE="$PID_DIR/worker.pid"

# 工具函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 优雅停止进程
stop_process() {
    local pid_file=$1
    local service_name=$2
    local force=${3:-false}
    
    if [ ! -f "$pid_file" ]; then
        log_warning "$service_name: PID 文件不存在，可能未运行"
        return 0
    fi
    
    local pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [ -z "$pid" ]; then
        log_warning "$service_name: PID 文件为空"
        rm -f "$pid_file"
        return 0
    fi
    
    if ! kill -0 "$pid" 2>/dev/null; then
        log_warning "$service_name: 进程 $pid 不存在（可能已停止）"
        rm -f "$pid_file"
        return 0
    fi
    
    log_info "停止 $service_name (PID: $pid)..."
    
    if [ "$force" = "true" ]; then
        # 强制终止
        kill -9 "$pid" 2>/dev/null || true
        log_success "$service_name 已强制终止"
    else
        # 优雅停止：先发送 SIGTERM，等待进程退出
        kill -TERM "$pid" 2>/dev/null || true
        
        # 等待进程退出（最多 10 秒）
        local count=0
        while [ $count -lt 10 ]; do
            if ! kill -0 "$pid" 2>/dev/null; then
                log_success "$service_name 已优雅停止"
                rm -f "$pid_file"
                return 0
            fi
            sleep 1
            count=$((count + 1))
        done
        
        # 如果还在运行，强制终止
        log_warning "$service_name 未在 10 秒内退出，强制终止..."
        kill -9 "$pid" 2>/dev/null || true
        log_success "$service_name 已强制终止"
    fi
    
    rm -f "$pid_file"
}

# 停止所有相关进程（通过端口）
stop_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti ":$port" 2>/dev/null || echo "")
    if [ -z "$pids" ]; then
        return 0
    fi
    
    log_info "发现端口 $port 上的进程，正在停止 $service_name..."
    for pid in $pids; do
        # 检查进程命令是否匹配
        local cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
        if [[ "$cmd" == *"python"* ]] || [[ "$cmd" == *"node"* ]] || [[ "$cmd" == *"next"* ]]; then
            log_info "停止进程 $pid ($cmd)..."
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
    done
}

# 清理 PID 目录
cleanup_pid_dir() {
    if [ -d "$PID_DIR" ]; then
        local remaining_files=$(find "$PID_DIR" -name "*.pid" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$remaining_files" -eq 0 ]; then
            log_info "清理空的 PID 目录..."
            rmdir "$PID_DIR" 2>/dev/null || true
        fi
    fi
}

# 主程序
cd "$PROJECT_ROOT"

echo "🛑 墨径 (InkPath) 系统关闭脚本"
echo "=============================="
echo ""

# 检查是否使用强制模式
FORCE=false
if [ "${1:-}" = "--force" ] || [ "${1:-}" = "-f" ]; then
    FORCE=true
    log_warning "使用强制模式停止服务"
fi

# 停止服务
log_info "正在停止服务..."

# 停止 Flask
stop_process "$FLASK_PID_FILE" "Flask API" "$FORCE"

# 停止 Next.js
stop_process "$NEXTJS_PID_FILE" "Next.js 前端" "$FORCE"

# 停止 Worker（如果存在）
if [ -f "$WORKER_PID_FILE" ]; then
    stop_process "$WORKER_PID_FILE" "RQ Worker" "$FORCE"
fi

# 通过端口检查并停止（兜底方案）
if [ "$FORCE" = "true" ]; then
    log_info "检查并清理端口占用..."
    stop_by_port 5002 "Flask API"
    stop_by_port 5001 "Next.js"
fi

# 清理 PID 目录
cleanup_pid_dir

echo ""
log_success "所有服务已停止"
echo ""

# 询问是否停止 Docker 服务
read -p "是否停止 Docker 服务 (PostgreSQL, Redis)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "停止 Docker 服务..."
    if docker-compose down 2>/dev/null; then
        log_success "Docker 服务已停止"
    else
        log_warning "Docker 服务停止失败或未运行"
    fi
fi

echo ""
log_success "关闭完成！"
