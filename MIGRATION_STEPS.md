# 迁移步骤（最简单的方

## 问题
数据库缺少 `starter` 列。

## 解决方案

在 **Render 后台 Shell** 中执行：

```bash
cd /opt/render/project/src
python migrations/run_migration.py
```

如果 Python 脚本也失败，尝试：

```bash
# 1. 重启服务
# 在 Render Dashboard 点击 "Manual Deploy"

# 2. 重启后再试
cd /opt/render/project/src
python migrations/run_migration.py

# 3. 如果还是不行，使用原始 SQL
psql "$DATABASE_URL" -c "ALTER TABLE stories ADD COLUMN starter TEXT NULL;"
```

## 验证

成功后重启服务：
1. Dashboard → inkpath-api
2. Manual Deploy → Deploy latest commit

## 测试 API

```bash
curl "https://inkpath-api.onrender.com/api/v1/stories?limit=1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

应该返回故事列表。
