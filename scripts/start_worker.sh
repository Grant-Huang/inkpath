#!/bin/bash

# 启动RQ Worker处理通知队列

echo "=========================================="
echo "启动RQ Worker (通知队列)"
echo "=========================================="
echo ""

# 检查Redis是否运行
REDIS_RUNNING=false

# 尝试通过Docker检查
if docker ps --filter "name=inkpath_redis" --format "{{.Names}}" | grep -q "inkpath_redis"; then
    REDIS_RUNNING=true
    echo "✅ Redis (Docker) 运行正常"
elif command -v redis-cli > /dev/null 2>&1 && redis-cli ping > /dev/null 2>&1; then
    REDIS_RUNNING=true
    echo "✅ Redis (本地) 运行正常"
fi

if [ "$REDIS_RUNNING" = false ]; then
    echo "❌ Redis未运行，请先启动Redis:"
    echo "   docker-compose up -d redis"
    echo "   或"
    echo "   redis-server"
    exit 1
fi

echo ""

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  未找到虚拟环境，使用系统Python"
fi

echo ""

# 设置环境变量
export FLASK_APP=src.app:create_app
export FLASK_ENV=${FLASK_ENV:-development}

# 显示配置信息
echo "配置信息:"
echo "  Redis Host: ${REDIS_HOST:-localhost}"
echo "  Redis Port: ${REDIS_PORT:-6379}"
echo "  Redis DB: ${REDIS_DB:-0}"
echo ""

# 启动RQ Worker
echo "🚀 启动RQ Worker..."
echo "   队列名称: notifications"
echo "   按 Ctrl+C 停止"
echo ""

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动Worker
cd "$(dirname "$0")/.." || exit 1

rq worker notifications \
    --url "redis://${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}/${REDIS_DB:-0}" \
    --name "inkpath-notification-worker" \
    --verbose \
    --with-scheduler
