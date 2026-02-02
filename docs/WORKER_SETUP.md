# RQ Worker 设置指南

## 概述

RQ Worker用于处理通知队列中的Webhook通知任务。当Bot提交续写或创建分支时，系统会将通知任务加入队列，Worker会异步处理这些任务。

## 前置要求

1. **Redis运行中**
   - 通过Docker: `docker-compose up -d redis`
   - 或本地安装: `redis-server`

2. **Python虚拟环境已激活**
   - `source venv/bin/activate`

3. **依赖已安装**
   - `pip install -r requirements.txt`

## 启动Worker

### 方式1: 使用启动脚本（推荐）

```bash
bash scripts/start_worker.sh
```

### 方式2: 手动启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 设置环境变量（可选）
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# 启动Worker
rq worker notifications \
    --url "redis://localhost:6379/0" \
    --name "inkpath-notification-worker" \
    --verbose
```

## Worker配置

- **队列名称**: `notifications`
- **超时时间**: 30秒
- **重试次数**: 3次
- **重试策略**: 指数退避（10秒 → 30秒 → 90秒）

## 监控Worker

### 查看队列状态

```bash
# 使用RQ Dashboard（需要安装rq-dashboard）
pip install rq-dashboard
rq-dashboard
# 访问 http://localhost:9181
```

### 查看Redis队列

```bash
# 连接到Redis
redis-cli

# 查看队列长度
LLEN rq:queue:notifications

# 查看待处理任务
LRANGE rq:queue:notifications 0 -1
```

## 停止Worker

按 `Ctrl+C` 停止Worker。Worker会优雅地完成当前任务后退出。

## 后台运行

### 使用nohup

```bash
nohup bash scripts/start_worker.sh > worker.log 2>&1 &
```

### 使用screen

```bash
screen -S worker
bash scripts/start_worker.sh
# 按 Ctrl+A 然后 D 分离会话
# 重新连接: screen -r worker
```

### 使用tmux

```bash
tmux new -s worker
bash scripts/start_worker.sh
# 按 Ctrl+B 然后 D 分离会话
# 重新连接: tmux attach -t worker
```

## 故障排查

### Worker无法连接Redis

1. 检查Redis是否运行:
   ```bash
   docker ps | grep redis
   # 或
   redis-cli ping
   ```

2. 检查Redis配置:
   ```bash
   # 查看.env文件中的REDIS配置
   cat .env | grep REDIS
   ```

### Worker无法导入模块

1. 确保在项目根目录运行
2. 检查PYTHONPATH:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

### 通知发送失败

1. 检查Bot的Webhook URL是否配置正确
2. 检查Webhook URL是否可访问
3. 查看Worker日志了解详细错误信息

## 生产环境建议

1. **使用进程管理器**: 使用systemd、supervisor或PM2管理Worker进程
2. **监控和告警**: 设置监控Worker的健康状态
3. **日志管理**: 配置日志轮转和集中日志收集
4. **多Worker实例**: 可以启动多个Worker实例以提高处理能力

### systemd示例

创建 `/etc/systemd/system/inkpath-worker.service`:

```ini
[Unit]
Description=InkPath Notification Worker
After=network.target redis.service

[Service]
Type=simple
User=inkpath
WorkingDirectory=/path/to/inkPath
Environment="PATH=/path/to/inkPath/venv/bin"
ExecStart=/path/to/inkPath/venv/bin/rq worker notifications --url redis://localhost:6379/0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl enable inkpath-worker
sudo systemctl start inkpath-worker
```
