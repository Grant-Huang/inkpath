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
alembic upgrade head 2>/dev/null || echo "No migrations to run or alembic not available"

# 启动Gunicorn
echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:$PORT "src.app:create_app()"
