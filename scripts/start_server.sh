#!/bin/bash
# 启动Flask开发服务器

cd "$(dirname "$0")/.."
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "🚀 启动Flask开发服务器..."
echo "端口: 5001"
echo "访问: http://localhost:5001/api/v1/health"
echo ""

python src/app.py
