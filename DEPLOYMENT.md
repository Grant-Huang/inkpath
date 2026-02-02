# InkPath 部署指南

## 方式一：Vercel（推荐 - 免费）

### 1. 准备GitHub仓库

确保代码已推送到GitHub：
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Vercel部署步骤

1. **登录Vercel**
   - 访问 https://vercel.com
   - 用GitHub账号登录

2. **导入项目**
   - 点击 "Add New..." → "Project"
   - 选择 "Import Git Repository"
   - 选择你的 `inkpath` 仓库

3. **配置项目**
   - Framework Preset: `Next.js` (应该自动识别)
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

4. **环境变量** (重要!)
   - 在项目设置中添加：
     ```
     NEXT_PUBLIC_DEMO_MODE = true
     ```
   - 这会启用演示模式，使用mock数据，无需后端

5. **部署**
   - 点击 "Deploy"
   - 等待构建完成（约1-2分钟）

6. **获取访问地址**
   - 部署成功后，Vercel会显示访问URL
   - 格式如：`https://inkpath-xxx.vercel.app`

### 3. 自动部署

每次推送到main分支，Vercel会自动重新部署。

---

## 方式二：Netlify（替代方案）

1. 访问 https://netlify.com
2. 用GitHub登录
3. "Add new site" → "Import an existing project"
4. 选择 `inkpath` 仓库
5. 配置：
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `.next`
6. 添加环境变量：`NEXT_PUBLIC_DEMO_MODE=true`
7. 部署

---

## 演示模式 vs 完整模式

### 演示模式（当前配置）
- ✅ **完全免费**
- ✅ 无需数据库
- ✅ 无需后端服务器
- ❌ 数据不持久化（刷新页面后重置）
- ❌ 部分功能不可用（创建故事、投票等）

**启用方式：** 设置环境变量 `NEXT_PUBLIC_DEMO_MODE=true`

### 完整模式（需要付费资源）
- ✅ 完整功能
- ✅ 数据持久化
- ❌ 需要PostgreSQL数据库
- ❌ 需要Redis缓存
- ❌ 需要后端服务器

**部署方案：**
- 前端：Vercel (免费)
- 后端：Railway/Render (付费)
- 数据库：Supabase/Neon (免费额度)

---

## 快速测试（本地）

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

---

## 当前状态

- ✅ 前端构建成功
- ✅ 演示模式配置完成
- ✅ GitHub Actions配置完成
- ⏳ 需要手动配置Vercel部署

**部署日志：** `OPTIMIZATION_LOG.md`

---

## 常见问题

**Q: 页面加载慢？**
A: 演示模式首次加载可能较慢，后续有缓存。

**Q: 看不到故事内容？**
A: 确保 `NEXT_PUBLIC_DEMO_MODE=true` 环境变量已设置。

**Q: 如何启用完整功能？**
A: 需要部署完整后端（Flask + PostgreSQL + Redis），这需要付费资源。
