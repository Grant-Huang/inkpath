#!/bin/bash
# 启动脚本 - 自动运行数据库迁移后启动应用

set -e

echo "=== InkPath Backend Starting ==="

# 进入项目目录
cd /opt/render/project/src

# 安装依赖
echo "Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null || true

# 运行数据库迁移
echo "Running database migrations..."
echo "Checking alembic configuration..."
alembic current 2>&1 || true
echo ""
echo "Checking available migrations..."
alembic history --verbose 2>&1 | head -20 || true
echo ""
echo "Upgrading to latest..."
alembic upgrade heads 2>&1 || echo "Migration failed - continuing anyway"

# 启动Gunicorn
echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:$PORT "src.app:create_app()"
