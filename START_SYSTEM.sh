#!/bin/bash
# 墨径系统一键启动脚本（容错增强版）

set -euo pipefail  # 严格模式：遇到错误立即退出，未定义变量报错，管道错误也会被捕获

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
LOG_DIR="$PROJECT_ROOT/logs"
FLASK_PORT=5002
NEXTJS_PORT=5001
FLASK_PID_FILE="$PID_DIR/flask.pid"
NEXTJS_PID_FILE="$PID_DIR/nextjs.pid"
FLASK_LOG="$LOG_DIR/flask.log"
NEXTJS_LOG="$LOG_DIR/nextjs.log"

# 创建必要的目录
mkdir -p "$PID_DIR" "$LOG_DIR"

# 清理函数
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}❌ 启动过程中发生错误，退出码: $exit_code${NC}"
        echo "正在清理..."
        # 只清理本次启动的进程
        if [ -f "$FLASK_PID_FILE" ]; then
            local pid=$(cat "$FLASK_PID_FILE" 2>/dev/null || echo "")
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$FLASK_PID_FILE"
        fi
        if [ -f "$NEXTJS_PID_FILE" ]; then
            local pid=$(cat "$NEXTJS_PID_FILE" 2>/dev/null || echo "")
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$NEXTJS_PID_FILE"
        fi
    fi
}
trap cleanup EXIT ERR

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

# 检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    if lsof -i ":$port" >/dev/null 2>&1; then
        local process=$(lsof -ti ":$port" | head -1)
        if [ -n "$process" ]; then
            local cmd=$(ps -p "$process" -o comm= 2>/dev/null || echo "unknown")
            log_warning "端口 $port 已被占用 (PID: $process, 命令: $cmd)"
            # 检查是否是我们的进程
            if [ -f "$PID_DIR/${service_name}.pid" ]; then
                local saved_pid=$(cat "$PID_DIR/${service_name}.pid" 2>/dev/null || echo "")
                if [ "$saved_pid" = "$process" ]; then
                    log_info "这是之前启动的 $service_name 进程，将使用现有进程"
                    return 2  # 已运行
                fi
            fi
            return 1  # 被其他进程占用
        fi
    fi
    return 0  # 端口可用
}

# 检查进程是否运行
is_process_running() {
    local pid_file=$1
    local service_name=$2
    if [ ! -f "$pid_file" ]; then
        return 1
    fi
    local pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [ -z "$pid" ]; then
        return 1
    fi
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        log_warning "$service_name 的 PID 文件存在但进程不存在，清理 PID 文件"
        rm -f "$pid_file"
        return 1
    fi
}

# 等待服务就绪
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    log_info "等待 $service_name 启动..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            log_success "$service_name 已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
        echo -n "."
    done
    echo ""
    log_error "$service_name 启动超时（${max_attempts}秒）"
    return 1
}

# 健康检查
health_check() {
    local url=$1
    local service_name=$2
    if curl -s -f "$url" >/dev/null 2>&1; then
        log_success "$service_name 健康检查通过"
        return 0
    else
        log_error "$service_name 健康检查失败"
        return 1
    fi
}

# 主程序开始
cd "$PROJECT_ROOT"

echo "🚀 墨径 (InkPath) 系统启动脚本（容错增强版）"
echo "=========================================="
echo ""

# 检查 Docker
log_info "检查 Docker..."
if ! docker info >/dev/null 2>&1; then
    log_error "Docker 未运行，请先启动 Docker Desktop"
    echo "   运行: open -a Docker"
    exit 1
fi
log_success "Docker 运行正常"

# 检查虚拟环境
log_info "检查 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    log_warning "虚拟环境不存在，正在创建..."
    python3 -m venv venv || {
        log_error "创建虚拟环境失败"
        exit 1
    }
    log_success "虚拟环境已创建"
fi

# 激活虚拟环境
log_info "激活虚拟环境..."
source venv/bin/activate || {
    log_error "激活虚拟环境失败"
    exit 1
}

# 安装依赖
if [ ! -f "venv/.deps_installed" ]; then
    log_info "安装 Python 依赖..."
    pip install -q -r requirements.txt || {
        log_error "安装依赖失败"
        exit 1
    }
    touch venv/.deps_installed
    log_success "依赖安装完成"
fi

# 启动数据库
log_info "启动数据库和 Redis..."
if ! ./scripts/start_db.sh; then
    log_error "数据库启动失败"
    exit 1
fi
log_success "数据库服务已启动"

# 运行迁移
log_info "运行数据库迁移..."
if ! alembic upgrade head; then
    log_error "数据库迁移失败"
    exit 1
fi
log_success "数据库迁移完成"

# 检查 Flask 是否已运行
log_info "检查 Flask API 服务..."
if is_process_running "$FLASK_PID_FILE" "Flask"; then
    log_warning "Flask 已在运行，跳过启动"
    FLASK_PID=$(cat "$FLASK_PID_FILE")
else
    # 检查端口
    check_port $FLASK_PORT "flask"
    port_status=$?
    if [ $port_status -eq 1 ]; then
        log_error "端口 $FLASK_PORT 被其他进程占用，无法启动 Flask"
        exit 1
    fi
    
    # 启动 Flask
    log_info "启动 Flask API (端口: $FLASK_PORT)..."
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export PORT=$FLASK_PORT
    
    nohup python src/app.py >> "$FLASK_LOG" 2>&1 &
    FLASK_PID=$!
    echo "$FLASK_PID" > "$FLASK_PID_FILE"
    
    # 等待 Flask 启动
    if ! wait_for_service "http://localhost:$FLASK_PORT/api/v1/health" "Flask API"; then
        log_error "Flask 启动失败，查看日志: $FLASK_LOG"
        rm -f "$FLASK_PID_FILE"
        exit 1
    fi
fi

# 检查 Next.js 是否已运行
log_info "检查 Next.js 前端服务..."
if is_process_running "$NEXTJS_PID_FILE" "Next.js"; then
    log_warning "Next.js 已在运行，跳过启动"
    NEXTJS_PID=$(cat "$NEXTJS_PID_FILE")
else
    # 检查端口
    check_port $NEXTJS_PORT "nextjs"
    port_status=$?
    if [ $port_status -eq 1 ]; then
        log_error "端口 $NEXTJS_PORT 被其他进程占用，无法启动 Next.js"
        exit 1
    fi
    
    # 检查前端依赖
    if [ ! -d "frontend/node_modules" ]; then
        log_info "安装前端依赖..."
        cd frontend
        if ! npm install --silent; then
            log_error "前端依赖安装失败"
            exit 1
        fi
        cd "$PROJECT_ROOT"
        log_success "前端依赖安装完成"
    fi
    
    # 启动 Next.js
    log_info "启动 Next.js 前端 (端口: $NEXTJS_PORT)..."
    cd frontend
    export PORT=$NEXTJS_PORT
    export BACKEND_API_URL="http://localhost:$FLASK_PORT"
    
    nohup npx next dev -p $NEXTJS_PORT >> "$NEXTJS_LOG" 2>&1 &
    NEXTJS_PID=$!
    echo "$NEXTJS_PID" > "$NEXTJS_PID_FILE"
    cd "$PROJECT_ROOT"
    
    # 等待 Next.js 启动
    sleep 3
    if ! wait_for_service "http://localhost:$NEXTJS_PORT" "Next.js"; then
        log_warning "Next.js 可能还在启动中，请稍后访问"
    fi
fi

# 最终健康检查
echo ""
log_info "执行最终健康检查..."
health_check "http://localhost:$FLASK_PORT/api/v1/health" "Flask API" || true
health_check "http://localhost:$NEXTJS_PORT" "Next.js" || true

# 显示启动信息
echo ""
echo "=========================================="
log_success "系统启动完成！"
echo "=========================================="
echo ""
echo "📌 访问地址："
echo "   前端页面: http://localhost:$NEXTJS_PORT"
echo "   API 健康检查: http://localhost:$FLASK_PORT/api/v1/health"
echo ""
echo "📝 日志文件："
echo "   Flask: $FLASK_LOG"
echo "   Next.js: $NEXTJS_LOG"
echo ""
echo "🆔 进程 ID："
echo "   Flask PID: $FLASK_PID (保存在 $FLASK_PID_FILE)"
echo "   Next.js PID: $NEXTJS_PID (保存在 $NEXTJS_PID_FILE)"
echo ""
echo "🛑 停止服务："
echo "   ./shutdown.sh"
echo "   或"
echo "   kill $FLASK_PID $NEXTJS_PID"
echo ""

# 成功，不触发 cleanup
trap - EXIT ERR
