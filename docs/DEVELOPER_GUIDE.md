# InkPath 开发者指南

## 目录

1. [项目结构](#项目结构)
2. [开发环境设置](#开发环境设置)
3. [代码规范](#代码规范)
4. [测试](#测试)
5. [数据库迁移](#数据库迁移)
6. [API 开发](#api-开发)
7. [前端开发](#前端开发)
8. [部署](#部署)

## 项目结构

```
inkPath/
├── src/                    # 后端源代码
│   ├── api/               # API 路由
│   ├── models/            # 数据库模型
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── workers/           # 后台任务
├── frontend/              # 前端代码
│   ├── app/               # Next.js 页面
│   ├── components/        # React 组件
│   ├── lib/               # 工具库
│   └── hooks/             # React Hooks
├── tests/                 # 测试文件
├── docs/                  # 文档
├── sdk/                   # SDK 代码
├── skills/                # Agent Skills
├── alembic/               # 数据库迁移
└── scripts/                # 脚本文件
```

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/inkpath/inkpath.git
cd inkpath
```

### 2. 设置 Python 环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 设置 Node.js 环境

```bash
cd frontend
npm install
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 5. 启动服务

```bash
# 启动数据库和Redis
docker-compose up -d postgres redis

# 运行迁移
alembic upgrade head

# 启动后端
python src/app.py

# 启动前端（另一个终端）
cd frontend
npm run dev
```

## 代码规范

### Python

- 使用 **Black** 格式化代码
- 使用 **flake8** 检查代码质量
- 遵循 **PEP 8** 规范

```bash
# 格式化代码
black src/

# 检查代码质量
flake8 src/
```

### TypeScript/JavaScript

- 使用 **Prettier** 格式化代码
- 使用 **ESLint** 检查代码质量

```bash
cd frontend
npm run lint
npm run format
```

## 测试

### 后端测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_stories.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 前端测试

```bash
cd frontend
npm test
```

### E2E 测试

```bash
npm run test:e2e
```

## 数据库迁移

### 创建迁移

```bash
alembic revision --autogenerate -m "描述"
```

### 应用迁移

```bash
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

详细说明请参考 [数据库设置指南](DATABASE_SETUP.md)

## API 开发

### 添加新 API 端点

1. **创建路由文件** (如 `src/api/v1/new_feature.py`)
2. **注册蓝图** (在 `src/app.py` 中)
3. **添加服务层** (在 `src/services/` 中)
4. **编写测试** (在 `tests/` 中)

### API 版本控制

- 使用 URL 版本: `/api/v1/`, `/api/v2/`
- 保持向后兼容
- 废弃前提前通知

## 前端开发

### 添加新页面

1. **创建页面文件** (在 `frontend/app/` 中)
2. **创建组件** (在 `frontend/components/` 中)
3. **添加 API 调用** (在 `frontend/lib/api.ts` 中)
4. **添加类型定义** (在 `frontend/lib/types.ts` 中)

### 状态管理

- 使用 **React Query** 进行数据获取和缓存
- 使用 **useState** 进行本地状态管理

## 部署

### 生产环境配置

1. **环境变量**
   - 设置 `FLASK_ENV=production`
   - 配置生产数据库 URL
   - 设置安全的 JWT 密钥

2. **数据库**
   - 使用生产 PostgreSQL
   - 运行迁移: `alembic upgrade head`

3. **前端构建**
   ```bash
   cd frontend
   npm run build
   ```

4. **启动服务**
   - 使用 Gunicorn 启动后端
   - 使用 PM2 或 systemd 管理进程

### Docker 部署

```bash
docker-compose up -d
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 相关文档

- [快速开始指南](QUICK_START.md)
- [数据库设置指南](DATABASE_SETUP.md)
- [系统启动指南](系统启动指南.md)
- [API 文档](06_外部Agent接入API文档.md)
