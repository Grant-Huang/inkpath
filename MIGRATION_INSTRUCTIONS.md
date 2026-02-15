# Render 后台迁移指南

## 问题

```
psycopg.errors.UndefinedColumn: column stories.starter does not exist
```

数据库缺少 `starter` 列。

## 解决方案

在 Render 后台 Shell 中执行以下命令：

### 方法 1: 使用 psql（推荐）

```bash
# 1. 进入项目目录
cd /opt/render/project/src

# 2. 运行迁移
psql "$DATABASE_URL" -c "ALTER TABLE stories ADD COLUMN starter TEXT NULL;"

# 3. 验证
psql "$DATABASE_URL" -c "\d stories" | grep starter
```

### 方法 2: 使用 Python 迁移脚本

```bash
cd /opt/render/project/src
source .venv/bin/activate
python migrations/add_starter_simple.py
```

## 验证迁移

```bash
psql "$DATABASE_URL" -c "SELECT column_name FROM information_schema.columns WHERE table_name='stories' AND column_name='starter';"
```

如果返回 `starter`，说明迁移成功。

## 重启服务

1. 访问 https://dashboard.render.com
2. 找到 inkpath-api 服务
3. 点击 "Manual Deploy" → "Deploy latest commit"

## 验证 API 恢复

```bash
curl -s "https://inkpath-api.onrender.com/api/v1/stories?limit=1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
