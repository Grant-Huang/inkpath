# G-access 摘要生成测试指南

## 概述

本目录包含两个测试脚本，用于测试使用 G-access 生成故事进展摘要的功能。

## 脚本说明

### 1. `test_gaccess_summary_simple.py` - 简单 API 连接测试

**用途**: 测试 G-access API 连接和基本功能，不需要数据库连接。

**使用方法**:
```bash
# 设置环境变量
export GACCESS_URL='https://your-gaccess-url.com'
export GACCESS_TOKEN='your-token'

# 运行测试
python scripts/test_gaccess_summary_simple.py
```

**特点**:
- ✅ 不需要数据库连接
- ✅ 快速测试 API 是否可用
- ✅ 使用测试数据生成摘要

### 2. `test_gaccess_summary.py` - 完整功能测试

**用途**: 测试使用真实分支数据生成摘要，需要数据库连接。

**使用方法**:
```bash
# 设置环境变量
export GACCESS_URL='https://your-gaccess-url.com'
export GACCESS_TOKEN='your-token'
export DATABASE_URL='postgresql://user:password@host:port/dbname'

# 测试指定分支
python scripts/test_gaccess_summary.py <branch_id>

# 自动选择第一个有续写段的分支
python scripts/test_gaccess_summary.py
```

**特点**:
- ✅ 使用真实的分支和续写段数据
- ✅ 可以指定分支 ID
- ✅ 显示完整的摘要信息（更新时间、覆盖段数等）

## 环境变量配置

### 必需的环境变量

- `GACCESS_URL`: G-access API 的 URL（例如: `https://gaccess.inkpath.cc`）
- `GACCESS_TOKEN`: G-access 的认证 Token

### 可选的环境变量

- `LLM_PROVIDER`: LLM 提供商，默认为 `gaccess`
- `DATABASE_URL`: 数据库连接字符串（仅完整测试需要）

## 示例

### 示例 1: 简单 API 测试

```bash
export GACCESS_URL='https://gaccess.inkpath.cc'
export GACCESS_TOKEN='your-secret-token'
python scripts/test_gaccess_summary_simple.py
```

**预期输出**:
```
============================================================
G-access API 测试
============================================================
GACCESS_URL: https://gaccess.inkpath.cc
GACCESS_TOKEN: ✅ 已配置

发送测试请求...
URL: https://gaccess.inkpath.cc/api/gemini

请求内容:
  Prompt长度: 234 字符

响应状态码: 200
✅ API 调用成功!

------------------------------------------------------------
生成的摘要:
------------------------------------------------------------
[生成的摘要内容...]
------------------------------------------------------------

摘要长度: 456 字符
```

### 示例 2: 测试指定分支

```bash
export GACCESS_URL='https://gaccess.inkpath.cc'
export GACCESS_TOKEN='your-secret-token'
export DATABASE_URL='postgresql://user:pass@localhost:5432/inkpath'

python scripts/test_gaccess_summary.py 3e92845b-68fa-4a8a-9517-d248792759c3
```

### 示例 3: 自动选择分支

```bash
export GACCESS_URL='https://gaccess.inkpath.cc'
export GACCESS_TOKEN='your-secret-token'
export DATABASE_URL='postgresql://user:pass@localhost:5432/inkpath'

python scripts/test_gaccess_summary.py
```

## 故障排除

### 问题 1: "G-access 未配置"

**原因**: 环境变量未设置

**解决方法**:
```bash
export GACCESS_URL='your-url'
export GACCESS_TOKEN='your-token'
```

### 问题 2: "API 返回错误状态码"

**可能原因**:
- Token 无效
- URL 不正确
- API 服务不可用

**解决方法**:
- 检查 Token 是否正确
- 验证 URL 是否可以访问
- 查看 API 服务状态

### 问题 3: "API 返回空内容"

**可能原因**:
- API 响应格式不符合预期
- Gemini API 返回了错误

**解决方法**:
- 检查 API 响应格式
- 查看完整响应内容（脚本会输出）

### 问题 4: "ModuleNotFoundError: No module named 'psycopg'"

**原因**: 数据库驱动未安装（仅完整测试需要）

**解决方法**:
```bash
pip install psycopg2-binary
# 或
pip install psycopg
```

## API 响应格式

G-access API 应该返回以下格式的 JSON:

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "生成的摘要内容..."
          }
        ]
      }
    }
  ]
}
```

## 相关文件

- `src/services/summary_service.py`: 摘要生成服务实现
- `src/config.py`: 配置管理
- `src/api/v1/summaries.py`: 摘要 API 端点

## 注意事项

1. G-access API 有超时限制（60秒），如果生成时间过长可能会失败
2. 确保 Token 有足够的权限访问 G-access API
3. 测试时建议使用较小的续写段数量，避免超时
