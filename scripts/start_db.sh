#!/bin/bash
# 启动PostgreSQL和Redis数据库

echo "🚀 启动数据库服务..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon未运行"
    echo ""
    echo "请先启动Docker Desktop，然后重新运行此脚本"
    echo "或者运行: open -a Docker"
    exit 1
fi

# 启动PostgreSQL和Redis
echo "📦 启动PostgreSQL和Redis容器..."
docker-compose up -d postgres redis

# 等待数据库启动
echo "⏳ 等待数据库启动（10秒）..."
sleep 10

# 检查PostgreSQL是否就绪
echo "🔍 检查PostgreSQL连接..."
for i in {1..30}; do
    if docker exec inkpath_postgres pg_isready -U inkpath > /dev/null 2>&1; then
        echo "✅ PostgreSQL已就绪!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL启动超时"
        exit 1
    fi
    sleep 1
done

# 测试连接
echo "🧪 测试数据库连接..."
python scripts/test_db_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 数据库配置完成!"
    echo ""
    echo "下一步: 运行数据库迁移"
    echo "  alembic upgrade head"
else
    echo "❌ 数据库连接失败，请检查配置"
    exit 1
fi
