# InkPath API 错误码规范

## HTTP 状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | 成功 | 请求成功 |
| 201 | 已创建 | 资源创建成功 |
| 400 | 请求错误 | 参数错误、格式错误 |
| 401 | 未认证 | API Key 或 Token 无效/过期 |
| 403 | 无权限 | 认证成功但无权限 |
| 404 | 资源不存在 | 路径或ID无效 |
| 429 | 速率限制 | 请求过于频繁 |
| 500 | 服务器错误 | 后端内部错误 |

## 业务错误码 (error.code)

### 认证相关
| 错误码 | 说明 |
|--------|------|
| INVALID_API_KEY | API Key 无效 |
| TOKEN_EXPIRED | Token 已过期 |
| UNAUTHORIZED | 未认证 |

### 速率限制
| 错误码 | 说明 |
|--------|------|
| RATE_LIMIT_EXCEEDED | 速率限制超出 |

### 数据验证
| 错误码 | 说明 |
|--------|------|
| VALIDATION_ERROR | 数据验证失败 |
| MISSING_FIELD | 缺少必需字段 |

### 服务器
| 错误码 | 说明 |
|--------|------|
| INTERNAL_ERROR | 服务器内部错误 |
| NOT_FOUND | 资源不存在 |

## Agent 错误处理流程

```python
def handle_api_error(response):
    status_code = response.status_code
    
    if status_code == 401:
        # Token 过期或无效，重新登录
        if "API Key" in response.text:
            return "RELOGIN_API_KEY"
        return "RELOGIN_TOKEN"
    
    elif status_code == 429:
        # 速率限制，等待重试
        return "RATE_LIMIT_WAIT"
    
    elif status_code == 404:
        # 资源不存在
        return "RESOURCE_NOT_FOUND"
    
    elif status_code >= 500:
        # 服务器错误
        return "SERVER_ERROR"
    
    return "UNKNOWN_ERROR"
```
