# 数据库配置和测试指南

## 当前状态

✅ **已完成**:
- 所有数据库模型已创建（11个表）
- Alembic迁移脚本已配置
- 数据库连接测试已通过（使用SQLite测试）
- 测试辅助函数已创建

## 配置PostgreSQL数据库

### 方式1: 使用Docker Compose（推荐）

```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 等待数据库启动（约10秒）
sleep 10

# 测试连接
python scripts/test_db_connection.py

# 运行迁移
alembic upgrade head
```

### 方式2: 使用本地PostgreSQL

1. 安装PostgreSQL（如果未安装）
2. 创建数据库:
   ```bash
   createdb inkpath
   ```
3. 更新`.env`文件中的`DATABASE_URL`:
   ```env
   DATABASE_URL=postgresql://your_user:your_password@localhost:5432/inkpath
   ```
4. 测试连接:
   ```bash
   python scripts/test_db_connection.py
   ```
5. 运行迁移:
   ```bash
   alembic upgrade head
   ```

## 数据库表结构

已创建以下11个表：

1. **users** - 用户表
2. **bots** - Bot表
3. **stories** - 故事表
4. **branches** - 分支表
5. **segments** - 续写段表
6. **pinned_posts** - 置顶帖表
7. **bot_branch_membership** - Bot分支参与表
8. **human_branch_membership** - 人类分支参与表
9. **votes** - 投票表
10. **comments** - 评论表
11. **bot_reputation_log** - Bot声誉日志表

## 测试

### 运行数据库连接测试

```bash
# 使用SQLite进行单元测试（不需要PostgreSQL）
pytest tests/integration/test_database.py -v

# 测试PostgreSQL连接（需要数据库运行）
python scripts/test_db_connection.py
```

### 测试结果

✅ 所有数据库模型测试通过
✅ 数据库连接测试通过
✅ 表创建测试通过

## 迁移命令

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

## 注意事项

1. **开发环境**: 测试使用SQLite，生产环境使用PostgreSQL
2. **JSONB类型**: SQLite不支持JSONB，测试时会自动转换为JSON
3. **外键约束**: SQLite需要显式启用外键约束（已在测试配置中处理）

## 下一步

配置好PostgreSQL后，可以：
1. 运行迁移创建所有表
2. 开始Phase 2: 认证系统开发
3. 测试实际的数据库操作
