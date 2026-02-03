# InkPath 部署配置

## 项目结构

```
inkpath/
├── frontend/          # Next.js前端 (部署到Vercel)
│   ├── app/           # Next.js 13+ App Router
│   ├── components/     # React组件
│   ├── hooks/         # 自定义Hooks
│   ├── lib/           # API客户端、工具函数
│   └── package.json   # 前端依赖
├── src/               # Flask后端 (部署到Render)
│   ├── api/           # API路由
│   ├── models/        # 数据库模型
│   ├── services/      # 业务逻辑
│   └── app.py         # Flask应用入口
├── requirements.txt   # Python依赖
└── .env              # 环境变量配置
```

---

## 一、Vercel部署前端

### 部署步骤

1. **登录Vercel**
   - 访问 https://vercel.com
   - 用GitHub账号登录

2. **导入项目**
   - 点击 "Add New..." → "Project"
   - 选择 "Import Git Repository"
   - 选择 `Grant-Huang/inkpath` 仓库

3. **配置项目**
   ```
   Framework Preset: Next.js (自动识别)
   Root Directory: frontend
   Build Command: npm install && npm run build
   Output Directory: .next
   ```

4. **设置环境变量** (在Vercel Dashboard → Settings → Environment Variables)
   ```
   NEXT_PUBLIC_API_URL=https://inkpath-backend.onrender.com
   NEXT_PUBLIC_DEMO_MODE=false
   ```

5. **部署**
   - 点击 "Deploy"
   - 等待构建完成（约2-3分钟）

6. **获取访问地址**
   - 格式: `https://inkpath-xxx.vercel.app`

### 验证

访问 https://your-frontend.vercel.app 应该能看到前端页面。

---

## 二、Render部署后端

### 部署步骤

1. **登录Render**
   - 访问 https://dashboard.render.com
   - 连接你的GitHub仓库

2. **创建Web Service**
   ```
   Name: inkpath-backend
   Root Directory: src
   Build Command: pip install -r requirements.txt
   Start Command: python src/app.py
   Plan: Free (或按需选择)
   ```

3. **创建托管数据库**
   - PostgreSQL: `inkpath-db` (Free tier)
   - Redis: `inkpath-redis` (Free tier)

4. **设置环境变量**
   ```
   DATABASE_URL=postgresql://user:pass@<host>:<port>/<dbname>
   REDIS_HOST=<redis-host>
   REDIS_PORT=6379
   REDIS_DB=0
   JWT_SECRET_KEY=<生成安全的随机字符串>
   FLASK_ENV=production
   FLASK_DEBUG=False
   PORT=5000
   CORS_ORIGINS=https://your-frontend.vercel.app
   BACKEND_API_URL=https://inkpath-backend.onrender.com
   ```

5. **运行数据库迁移**
   ```
   alembic upgrade head
   ```

6. **验证部署**
   访问: https://inkpath-backend.onrender.com/health

---

## 三、完整环境变量模板

### 前端环境变量 (Vercel)

| 变量名 | 值 | 说明 |
|-------|-----|------|
| `NEXT_PUBLIC_API_URL` | `https://inkpath-backend.onrender.com` | 后端API地址 |
| `NEXT_PUBLIC_DEMO_MODE` | `false` | 关闭演示模式 |

### 后端环境变量 (Render)

| 变量名 | 值 | 说明 |
|-------|-----|------|
| `DATABASE_URL` | `<render-postgresql-connection-string>` | PostgreSQL连接串 |
| `REDIS_HOST` | `<render-redis-host>` | Redis主机 |
| `REDIS_PORT` | `6379` | Redis端口 |
| `REDIS_DB` | `0` | Redis数据库编号 |
| `JWT_SECRET_KEY` | `<生成随机字符串>` | JWT密钥 (重要!) |
| `FLASK_ENV` | `production` | 生产环境 |
| `FLASK_DEBUG` | `false` | 关闭调试 |
| `PORT` | `5000` | 服务端口 |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | 允许的前端域名 |

---

## 四、部署验证

### 前端验证

1. 访问前端URL
2. 检查页面是否正常加载
3. 检查API请求是否成功（浏览器开发者工具Network标签）

### 后端验证

```bash
# 健康检查
curl https://inkpath-backend.onrender.com/health

# 预期响应
{"status": "healthy"}
```

---

## 五、常见问题

### Q1: 前端显示"加载失败"
A: 检查 `NEXT_PUBLIC_API_URL` 是否正确指向后端地址

### Q2: CORS错误
A: 在后端环境变量中设置 `CORS_ORIGINS` 为你的前端域名

### Q3: 数据库连接失败
A: 确认 `DATABASE_URL` 格式正确，且数据库已创建

### Q4: 忘记JWT_SECRET_KEY
A: 重新生成并更新Render环境变量

---

## 六、监控和维护

### Render监控
- 查看日志: Dashboard → Service → Logs
- 性能监控: Dashboard → Insights

### Vercel监控
- 查看部署: Dashboard → Deployments
- 分析: Dashboard → Analytics

---

## 七、架构图

```
用户请求
    ↓
┌─────────────────┐
│   Vercel        │ ← 前端静态资源 + SSR
│  (Frontend)     │
└────────┬────────┘
         │ API请求 (/api/*)
         ↓
┌─────────────────┐
│   Render        │ ← Flask后端
│  (Backend)      │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌───────┐  ┌───────┐
│PostgreSQL│  │ Redis │
└─────────┘  └───────┘
```

---

## 八、更新部署

### 更新前端
```bash
git add .
git commit -m "update"
git push origin main
# Vercel自动部署
```

### 更新后端
```bash
git add .
git commit -m "update backend"
git push origin main
# Render自动部署
```

---

**最后更新:** 2026-02-02
