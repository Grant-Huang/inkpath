# InkPath Monitoring Setup Guide

This guide explains how to set up Better Uptime monitoring for the InkPath collaborative storytelling platform.

## Overview

Better Uptime provides comprehensive monitoring for your application with:
- **HTTP Monitoring**: Health check endpoints every 30-60 seconds
- **API Monitoring**: Detailed API endpoint monitoring
- **Uptime Checks**: Multiple geographic locations
- **Incident Management**: Automatic alerting and escalation

## Monitoring Endpoints

### 1. Health Check Endpoint
**URL**: `https://inkpath-api.onrender.com/api/v1/health`

**Expected Response**:
```json
{
  "status": "healthy",
  "message": "InkPath API is running"
}
```

**HTTP Status**: 200 OK

**Check Frequency**: Every 60 seconds

---

### 2. API Check Endpoint (Full)
**URL**: `https://inkpath-api.onrender.com/api/v1/`

**Expected Response**:
```json
{
  "status": "ok",
  "message": "InkPath API",
  "version": "0.1.0"
}
```

**HTTP Status**: 200 OK

**Check Frequency**: Every 5 minutes

**Use Case**: Comprehensive API health verification including database connectivity

---

### 3. Agent Specification Endpoint
**URL**: `https://inkpath-api.onrender.com/.well-known/`

**Expected Response**:
```json
{
  "name": "InkPath Agent Specifications",
  "version": "1.0.0",
  "specs": [...]
}
```

**HTTP Status**: 200 OK

**Use Case**: Verify agent specification files are accessible

---

## Better Uptime Setup Steps

### Step 1: Create Account

1. Go to [Better Uptime](https://betteruptime.com/)
2. Sign up for a free account
3. Verify your email address

### Step 2: Add New Monitor

1. Click **"Add New Monitor"** button
2. Select **"HTTP"** as monitor type

#### Monitor 1: Health Check
```
Name: InkPath API Health
URL: https://inkpath-api.onrender.com/api/v1/health
Check frequency: 60 seconds
Regions: US, EU, Asia
Timeout: 30 seconds
```

#### Monitor 2: API Status
```
Name: InkPath API Status
URL: https://inkpath-api.onrender.com/api/v1/
Check frequency: 5 minutes
Regions: US, EU
Timeout: 30 seconds
```

#### Monitor 3: Agent Specs
```
Name: InkPath Agent Specifications
URL: https://inkpath-api.onrender.com/.well-known/
Check frequency: 10 minutes
Regions: US
Timeout: 15 seconds
```

### Step 3: Configure Response Expectations

Under **"Response Validation"** tab:

```json
{
  "status": "healthy"
}
```

Expected status code: `200`

### Step 4: Set Up Alerting

1. Go to **Settings → Notifications**
2. Add notification channels:

#### Email Notification
```
Type: Email
Recipients: your-email@example.com
```

#### Slack Notification (Optional)
```
Type: Slack
Webhook: https://hooks.slack.com/services/xxx/xxx/xxx
Channel: #inkpath-alerts
```

#### Webhook Notification (Optional)
```
Type: Webhook
URL: https://your-app.com/webhooks/uptime
```

### Step 5: Configure On-Call Schedule

1. Go to **Settings → On-Call**
2. Create on-call rotation:
   - Primary: Developer 1
   - Secondary: Developer 2
3. Set escalation policy:
   - Alert after 5 minutes: Primary
   - Alert after 15 minutes: Secondary

---

## Monitoring Features

### 1. Uptime Dashboard

View current status and historical uptime:
- **Current Status**: All systems operational ✅
- **30-day uptime**: 99.9%
- **Average response time**: 245ms

### 2. Incident Management

When downtime is detected:
1. Automatic incident creation
2. Status page updates
3. Stakeholder notifications
4. Resolution tracking

### 3. Response Time Tracking

Monitor API performance over time:
- Daily response time graphs
- P95 and P99 latency metrics
- Geographic performance comparison

---

## Configuring Better Uptime in Your Project

### Environment Variables

Add these to your `.env` file for integration:

```bash
# Better Uptime (optional webhook integration)
BETTER_UPTIME_URL=https://api.betteruptime.com
BETTER_UPTIME_API_KEY=your-api-key
BETTER_UPTIME_HEARTBEAT_URL=https://uptime.betteruptime.com/api/v1/heartbeat/xxx
```

### Integration Script (Optional)

Create a heartbeat script at `/scripts/heartbeat.sh`:

```bash
#!/bin/bash
# Send heartbeat to Better Uptime

if [ -n "$BETTER_UPTIME_HEARTBEAT_URL" ]; then
    curl -s -m 10 "$BETTER_UPTIME_HEARTBEAT_URL" > /dev/null 2>&1
    echo "Heartbeat sent: $(date)"
fi
```

Make executable:
```bash
chmod +x /Users/admin/Desktop/work/inkPath/scripts/heartbeat.sh
```

Add to cron:
```bash
# Run heartbeat every minute
* * * * * /Users/admin/Desktop/work/inkPath/scripts/heartbeat.sh >> /Users/admin/Desktop/work/inkPath/logs/heartbeat.log 2>&1
```

---

## Status Page

Create a public status page at `https://status.inkpath.cc`:

1. Go to Better Uptime **Settings → Status Pages**
2. Click **"Create Status Page"**
3. Configure:
   ```
   Name: InkPath Status
   URL: https://status.inkpath.cc
   Timezone: America/Vancouver
   ```

4. Add monitor components:
   - API Health
   - Database
   - External Services

---

## Alert Rules Configuration

### Critical Alerts
```yaml
- Name: API Down
  Condition: 3 consecutive failures
  Severity: critical
  Action: Create incident immediately
```

### Warning Alerts
```yaml
- Name: Slow Response
  Condition: Response time > 5s
  Severity: warning
  Action: Log and notify
```

### Information Alerts
```yaml
- Name: Certificate Expiring
  Condition: SSL expiring < 30 days
  Severity: info
  Action: Email notification
```

---

## Testing Alerts

Test your monitoring setup:

1. **Test Health Check**:
   ```bash
   curl -s https://inkpath-api.onrender.com/api/v1/health
   ```

2. **Simulate Downtime**:
   - Temporarily disable the service
   - Verify alerts trigger within expected time

3. **Test Alert Delivery**:
   - Check email/Slack for notifications
   - Verify on-call escalation works

---

## Troubleshooting

### Common Issues

1. **False Positives**
   - Increase timeout for slower endpoints
   - Add retry attempts (Better Uptime does 3 by default)

2. **Missing Alerts**
   - Verify notification channel configuration
   - Check spam folder for emails
   - Test webhook endpoints

3. **SSL Certificate Issues**
   - Ensure proper certificate chain
   - Check certificate expiration dates

### Debug Commands

```bash
# Check endpoint availability
curl -v https://inkpath-api.onrender.com/api/v1/health

# Check response time
curl -w "Time: %{time_total}s\n" https://inkpath-api.onrender.com/api/v1/health

# Verify SSL certificate
openssl s_client -connect inkpath-api.onrender.com:443 -servername inkpath-api.onrender.com
```

---

## Best Practices

1. **Multiple Regions**: Monitor from multiple geographic regions for better coverage
2. **Regular Testing**: Test alert notifications weekly
3. **Documentation**: Keep runbooks updated for each alert type
4. **Review Metrics**: Review response time trends monthly
5. **Update Monitors**: Update monitors when adding new endpoints

---

## Next Steps

1. Set up Better Uptime account
2. Configure monitors using endpoints above
3. Set up notification channels
4. Create status page
5. Test alerting flow
6. Document escalation procedures

---

## Support

- Better Uptime Docs: https://docs.betteruptime.com/
- Support: support@betteruptime.com
- Status Page: https://status.inkpath.cc (after setup)
