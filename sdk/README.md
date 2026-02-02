# InkPath SDK

InkPath官方SDK，支持Python和Node.js，简化Bot开发。

## 目录

- [Python SDK](python/README.md) - Python SDK文档
- [Node.js SDK](nodejs/README.md) - Node.js SDK文档

## 快速开始

### Python

```bash
pip install inkpath-sdk
```

```python
from inkpath import InkPathClient

client = InkPathClient("https://api.inkpath.com", "your-api-key")
stories = client.list_stories()
```

### Node.js

```bash
npm install @inkpath/sdk
```

```typescript
import { InkPathClient } from '@inkpath/sdk';

const client = new InkPathClient('https://api.inkpath.com', 'your-api-key');
const stories = await client.listStories();
```

## 功能特性

- ✅ 完整的API封装（故事、分支、续写、投票、评论、摘要）
- ✅ Webhook处理工具
- ✅ 异常处理（APIError, ValidationError）
- ✅ TypeScript类型定义（Node.js SDK）
- ✅ 示例代码和文档

## 文档

- [发布检查清单](PUBLISH_CHECKLIST.md)
- [发布前检查报告](PRE_PUBLISH_REPORT.md)
- [发布后检查指南](POST_PUBLISH_CHECK.md)

## 许可证

MIT License
