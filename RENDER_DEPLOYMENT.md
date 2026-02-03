# InkPath 后端部署配置 (Render)

## 部署步骤

### 1. 创建Render Web Service

1. 访问 https://dashboard.render.com
2. 连接你的GitHub仓库: Grant-Huang/inkpath
3. 配置如下：

**Basic Settings:**
- Name: `inkpath-backend`
- Root Directory: `src` (注意：不是根目录)
- Build Command: `pip install -r requirements.txt`
- Start Command: `python src/app.py`
- Plan: `Free` (或按需选择)

**Environment Variables:**

```bash
# Database (使用Render PostgreSQL)
DATABASE_URL=<render-postgresql-connection-string>

# Redis (使用Render Redis)
REDIS_HOST=<render-redis-host>
REDIS_PORT=6379
REDIS_DB=0

# JWT
JWT_SECRET_KEY=<generate-secure-random-string>

# Flask
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000

# CORS (允许前端访问)
CORS_ORIGINS=https://<your-vercel-frontend>.vercel.app

# API URL (供前端使用)
BACKEND_API_URL=https://<your-render-backend>.onrender.com
```

### 2. 创建托管数据库

1. 在Render Dashboard中创建:
   - **PostgreSQL**: `inkpath-db`
   - **Redis**: `inkpath-redis`

2. 创建完成后，将连接字符串添加到环境变量

### 3. 运行数据库迁移

首次部署后，需要运行数据库迁移：

```bash
# 通过Render CLI或Web Console执行
alembic upgrade head
```

### 4. 验证部署

访问: `https://<your-render-backend>.onrender.com/health`

---

## 本地测试

```bash
# 设置环境变量
export DATABASE_URL="postgresql://user:pass@localhost:5432/inkpath"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export JWT_SECRET_KEY="your-secret"

# 启动后端
python src/app.py
```

---

## 端口说明

- 开发环境: `http://localhost:5000`
- 生产环境: `https://<your-render-backend>.onrender.com`

## API端点

- 健康检查: `/health`
- API基础: `/api/v1/`
- 故事列表: `/api/v1/stories`
- 故事详情: `/api/v1/stories/:id`

---

## 故障排除

1. **启动失败**: 检查环境变量是否完整设置
2. **数据库连接失败**: 确认DATABASE_URL格式正确
3. **CORS错误**: 检查CORS_ORIGINS设置
4. **静态文件不加载**: 确认outputDirectory配置正确

## 监控

- 查看日志: Render Dashboard → Service → Logs
- 性能监控: Render Dashboard → Insights
