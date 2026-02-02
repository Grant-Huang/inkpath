# 快速启动指南

## 启动数据库

### 方式1: 使用启动脚本（推荐）

```bash
# 确保Docker Desktop已启动
open -a Docker  # macOS

# 运行启动脚本
./scripts/start_db.sh
```

### 方式2: 手动启动

```bash
# 1. 启动Docker Desktop（如果未运行）
open -a Docker  # macOS

# 2. 启动数据库容器
docker-compose up -d postgres redis

# 3. 等待数据库启动（约10秒）
sleep 10

# 4. 测试连接
python scripts/test_db_connection.py

# 5. 运行迁移
alembic upgrade head
```

## 运行迁移

```bash
# 应用所有迁移
alembic upgrade head

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

## 开发模式

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
pytest

# 启动开发服务器
python src/app.py
```

## 停止数据库

```bash
docker-compose down
```
