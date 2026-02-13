# InkPath 监控配置指南

> 本文档介绍如何设置 Better Uptime 监控，确保及时发现服务异常

---

## 目录

1. [为什么需要监控](#为什么需要监控)
2. [Better Uptime 简介](#better-uptime-简介)
3. [设置步骤](#设置步骤)
4. [监控配置](#监控配置)
5. [告警通知](#告警通知)
6. [备用方案](#备用方案)

---

## 为什么需要监控

当前 InkPath 部署在 Render Free  tier 上，存在以下问题：
- 服务响应慢（测试显示 26-84 秒）
- 容易挂起或超时
- 无法及时发现服务异常

通过监控可以：
- ✅ 及时发现服务宕机
- ✅ 跟踪服务可用性
- ✅ 收到邮件/短信告警
- ✅ 查看历史 uptime 数据

---

## Better Uptime 简介

**官网：** https://betteruptime.com/

**免费版功能：**
- ✅ 100 个监控点
- ✅ 每 5 分钟检查一次
- ✅ 邮件告警
- ✅ 7 天历史记录
- ✅ SSL 证书监控

**对比其他方案：**

| 服务 | 免费额 | 检查间隔 | 告警方式 |
|------|--------|----------|----------|
| Better Uptime | 100 点 | 5 分钟 | 邮件、短信(限) |
| UptimeRobot | 50 点 | 5 分钟 | 邮件、短信(限) |
| Pingdom | 1 点 | 1 分钟 | 邮件(限) |

**推荐理由：** Better Uptime 免费额度最充足，界面简洁，邮件通知稳定。

---

## 设置步骤

### 步骤 1：注册账号

1. 访问 https://betteruptime.com/
2. 点击 "Sign Up" 注册
3. 使用邮箱注册（推荐 Gmail）

### 步骤 2：添加监控

登录后，按照以下步骤添加监控：

#### 2.1 创建监控组（可选）

1. 点击左侧 "Heartbeats" → "New Heartbeat"（可选）
2. 名称输入：`inkpath-api`
3. 点击 "Create"

#### 2.2 添加 HTTP 监控

1. 点击左侧 "Monitors" → "New Monitor"
2. 选择类型：**HTTP(s)**

**监控配置：**

```
Monitor Type: HTTP(s)

URL to monitor:
- Primary: https://inkpath-api.onrender.com/api/v1/health
- Fallback: https://inkpath-api.onrender.com/api/v1/stories

Request timeout: 30 seconds

Check every: 5 minutes

Regions:
- ✅ North America
- ✅ Europe
- ✅ Asia (可选)

HTTP Method: GET

Expected status code: 200

Response should contain: "healthy" 或 "status":"success"

Headers: (可选)
- Authorization: Bearer YOUR_API_KEY  # 用于更详细的监控
```

**详细配置示例：**

```
Monitor Name: InkPath API - Health Check
URL: https://inkpath-api.onrender.com/api/v1/health
Method: GET
Timeout: 30
Check every: 5 minutes
Regions: North America, Europe
Expected status code: 200
Response contains: healthy
```

#### 2.3 添加备用监控

```
Monitor Name: InkPath API - Stories
URL: https://inkpath-api.onrender.com/api/v1/stories
Method: GET
Timeout: 30
Check every: 5 minutes
Regions: North America
Expected status code: 200
Response contains: success
```

### 步骤 3：配置告警

1. 点击左侧 "On-call" → "New On-call Schedule"
2. 添加告警规则：

```
Alert Rules:
- Name: InkPath Down Alert
- Trigger: When monitor is down for 2 checks (10 minutes)
- Notify via: Email
- Repeat every: 30 minutes until acknowledged
```

**详细配置：**

```
Escalation Policy:
1. Immediate notification
   - Method: Email
   - To: your-email@gmail.com
   - Delay: 0 minutes

2. Follow-up (if still down after 15 minutes)
   - Method: Email
   - To: your-email@gmail.com
   - Delay: 15 minutes
```

### 步骤 4：验证监控

1. 等待第一次检查（最多 5 分钟）
2. 查看 "Monitors" 页面状态
3. 确认收到告警邮件

---

## 监控配置

### 推荐的监控端点

| 端点 | 用途 | 期望响应 |
|------|------|----------|
| `/api/v1/health` | 服务健康检查 | `{"status":"healthy"}` |
| `/api/v1/stories` | API 可用性 | `{"status":"success"}` |
| `/api/v1/stories/{story_id}` | 故事详情 | `{"status":"success"}` |

### 高级配置（可选）

#### SSL 证书监控

Better Uptime 会自动监控 SSL 证书：

```
Monitor Type: SSL Certificate
URL: https://inkpath-api.onrender.com
Alert if: Certificate expires in less than 30 days
```

#### 自定义请求头

```
Headers:
- User-Agent: BetterUptime/1.0
- Accept: application/json
```

---

## 告警通知

### 邮件通知（免费）

```
To: your-email@gmail.com
Frequency: Immediate + Daily digest
```

### Slack 通知（可选）

1. 在 Slack 中创建 Incoming Webhook
2. 在 Better Uptime 中添加 Integration：
   - Settings → Integrations → Slack
   - Paste Webhook URL
3. 配置通知规则

### Webhook 通知（高级）

```
URL: https://your-server.com/webhook/better-uptime
Method: POST
Headers:
  Content-Type: application/json
  Authorization: Bearer YOUR_WEBHOOK_SECRET

Body:
{
  "event": "incident.created",
  "monitor": {
    "name": "InkPath API",
    "url": "https://inkpath-api.onrender.com/api/v1/health"
  },
  "incident": {
    "id": "12345",
    "started_at": "2024-01-01T00:00:00Z"
  }
}
```

---

## 备用方案

### 方案 1：UptimeRobot（免费 50 点）

**官网：** https://uptimerobot.com/

**设置步骤：**

1. 注册账号
2. Add New Monitor
3. 配置：
   ```
   Monitor Type: HTTP(s)
   URL: https://inkpath-api.onrender.com/api/v1/health
   Monitoring Interval: 5 minutes
   Timeout: 30 seconds
   ```
4. 添加告警邮箱

### 方案 2：Healthchecks.io（适合开发者）

**官网：** https://healthchecks.io/

**特点：**
- 适合监控定时任务
- 支持 cron job 监控
- 免费版 20 个检查

### 方案 3：自建监控（高级）

如果需要完全控制，可以考虑：

```
Stack:
- Prometheus + Grafana
- 或 Uptime Kuma (自托管)
```

**Uptime Kuma 部署：**

```bash
# 使用 Docker 部署
docker run -d --restart=always -p 3001:3001 -v uptime-kuma:/app/data --name uptime-kuma louislam/uptime-kuma

# 访问 http://localhost:3001
```

---

## 监控最佳实践

### 1. 多地点检查

```
Regions:
- North America (2 个节点)
- Europe (1 个节点)
- Asia (1 个节点)
```

避免单点故障。

### 2. 合理的超时时间

```
Timeout: 30 seconds
Checks: Every 5 minutes
```

Render Free tier 响应慢，设置 30s 超时比较合理。

### 3. 阶梯式告警

```
1. 第一次失败（5分钟）：记录
2. 连续2次失败（10分钟）：发送告警
3. 连续5次失败（25分钟）：升级通知
```

避免短暂网络波动触发告警。

### 4. 定期检查日志

```
每周检查：
- 告警历史
- 平均响应时间
- 失败率趋势
```

---

## 常见问题

### Q1: 收到太多告警怎么办？

**A:** 调整告警规则：
1. 增加 "连续失败次数" 阈值
2. 启用 "工作时间" 过滤
3. 设置告警冷却时间

### Q2: 监控显示 "Degraded" 但服务正常？

**A:** 可能原因：
1. 网络波动
2. 服务响应慢（Render Free tier 常见）
3. 检查超时设置

**解决：**
1. 增加超时时间到 30-60s
2. 添加备用监控端点

### Q3: 收不到邮件告警？

**A:** 检查：
1. 垃圾邮件箱
2. 邮箱设置 → 允许 betteruptime.com
3. Spam 黑名单

### Q4: 如何批量添加多个监控？

**A:** Better Uptime 支持 API：

```bash
curl -X POST "https://api.betteruptime.com/v2/monitors" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://inkpath-api.onrender.com/api/v1/health",
    "check_frequency": 5,
    "alert_threshold": 2,
    "http_method": "GET",
    "expected_status_code": 200
  }'
```

---

## 相关文档

- [部署文档](../RENDER_DEPLOYMENT.md)
- [故障排除文档](TROUBLESHOOTING.md)
- [性能优化文档](PERFORMANCE_OPTIMIZATION.md)

---

## 下一步行动

1. ✅ 阅读本文档
2. 🔲 注册 Better Uptime 账号
3. 🔲 添加监控端点
4. 🔲 配置告警通知
5. 🔲 测试告警功能
6. 🔲 记录监控状态

---

**最后更新：** 2026-02-12  
**维护者：** InkPath Team
