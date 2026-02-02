# SDK发布后检查指南

## 说明

本文档用于在SDK发布到PyPI和npm后，验证发布是否成功。

## Python SDK发布后检查

### 1. 安装测试

```bash
# 从PyPI安装
pip install inkpath-sdk

# 或从TestPyPI安装（测试环境）
pip install --index-url https://test.pypi.org/simple/ inkpath-sdk
```

**预期结果**: 安装成功，无错误

### 2. 导入测试

```bash
python -c "from inkpath import InkPathClient, WebhookHandler; print('✓ 导入成功')"
```

**预期结果**: 
```
✓ 导入成功
```

### 3. 功能测试

```python
# test_import.py
from inkpath import InkPathClient, WebhookHandler, APIError, ValidationError

# 测试客户端创建
client = InkPathClient('https://api.inkpath.com', 'test-key')
print('✓ 客户端创建成功')

# 测试可用方法
methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
print(f'✓ 可用方法数量: {len(methods)}')
print(f'✓ 主要方法: {methods[:5]}')

# 测试Webhook处理器
webhook = WebhookHandler()
print('✓ Webhook处理器创建成功')

print('\n✅ 所有基本功能测试通过')
```

**运行**:
```bash
python test_import.py
```

**预期结果**: 所有测试通过

### 4. 文档链接检查

访问PyPI页面: https://pypi.org/project/inkpath-sdk/

检查项:
- [ ] 项目描述正确
- [ ] README显示正确
- [ ] 版本号正确
- [ ] 下载链接可用
- [ ] 项目链接指向GitHub（如已设置）

## Node.js SDK发布后检查

### 1. 安装测试

```bash
# 从npm安装
npm install @inkpath/sdk

# 或全局安装（测试）
npm install -g @inkpath/sdk
```

**预期结果**: 安装成功，无错误

### 2. 导入测试（CommonJS）

```bash
node -e "const { InkPathClient } = require('@inkpath/sdk'); console.log('✓ 导入成功')"
```

**预期结果**: 
```
✓ 导入成功
```

### 3. 导入测试（ES Modules）

```javascript
// test_import.mjs
import { InkPathClient, WebhookHandler } from '@inkpath/sdk';

console.log('✓ ES Module导入成功');
console.log('✓ InkPathClient:', typeof InkPathClient);
console.log('✓ WebhookHandler:', typeof WebhookHandler);
```

**运行**:
```bash
node test_import.mjs
```

### 4. TypeScript类型测试

```typescript
// test_types.ts
import { InkPathClient, WebhookHandler, APIError, ValidationError } from '@inkpath/sdk';
import type { Story, Branch, Segment } from '@inkpath/sdk';

const client = new InkPathClient('https://api.inkpath.com', 'test-key');
console.log('✓ TypeScript类型检查通过');
```

**运行**:
```bash
npx tsc --noEmit test_types.ts
```

**预期结果**: 无类型错误

### 5. 功能测试

```javascript
// test_functionality.js
const { InkPathClient, WebhookHandler } = require('@inkpath/sdk');

// 测试客户端创建
const client = new InkPathClient('https://api.inkpath.com', 'test-key');
console.log('✓ 客户端创建成功');

// 测试Webhook处理器
const webhook = new WebhookHandler();
console.log('✓ Webhook处理器创建成功');

console.log('\n✅ 所有基本功能测试通过');
```

**运行**:
```bash
node test_functionality.js
```

### 6. 文档链接检查

访问npm页面: https://www.npmjs.com/package/@inkpath/sdk

检查项:
- [ ] 包描述正确
- [ ] README显示正确
- [ ] 版本号正确
- [ ] 下载统计可用
- [ ] 项目链接指向GitHub（如已设置）

## 完整检查脚本

### Python SDK

```bash
#!/bin/bash
# post_publish_check_python.sh

echo "=== Python SDK发布后检查 ==="

echo "1. 安装测试..."
pip install inkpath-sdk
if [ $? -eq 0 ]; then
    echo "✓ 安装成功"
else
    echo "✗ 安装失败"
    exit 1
fi

echo ""
echo "2. 导入测试..."
python -c "from inkpath import InkPathClient, WebhookHandler; print('✓ 导入成功')"
if [ $? -eq 0 ]; then
    echo "✓ 导入测试通过"
else
    echo "✗ 导入测试失败"
    exit 1
fi

echo ""
echo "3. 功能测试..."
python << EOF
from inkpath import InkPathClient, WebhookHandler
client = InkPathClient('https://api.inkpath.com', 'test-key')
webhook = WebhookHandler()
print('✓ 客户端创建成功')
print('✓ Webhook处理器创建成功')
EOF

echo ""
echo "✅ 所有检查通过"
```

### Node.js SDK

```bash
#!/bin/bash
# post_publish_check_nodejs.sh

echo "=== Node.js SDK发布后检查 ==="

echo "1. 安装测试..."
npm install @inkpath/sdk
if [ $? -eq 0 ]; then
    echo "✓ 安装成功"
else
    echo "✗ 安装失败"
    exit 1
fi

echo ""
echo "2. 导入测试..."
node -e "const { InkPathClient } = require('@inkpath/sdk'); console.log('✓ 导入成功')"
if [ $? -eq 0 ]; then
    echo "✓ 导入测试通过"
else
    echo "✗ 导入测试失败"
    exit 1
fi

echo ""
echo "3. 功能测试..."
node << EOF
const { InkPathClient, WebhookHandler } = require('@inkpath/sdk');
const client = new InkPathClient('https://api.inkpath.com', 'test-key');
const webhook = new WebhookHandler();
console.log('✓ 客户端创建成功');
console.log('✓ Webhook处理器创建成功');
EOF

echo ""
echo "4. TypeScript类型测试..."
echo "import { InkPathClient } from '@inkpath/sdk';" > test_types.ts
npx tsc --noEmit test_types.ts 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ 类型检查通过"
    rm test_types.ts
else
    echo "✗ 类型检查失败"
    rm test_types.ts
    exit 1
fi

echo ""
echo "✅ 所有检查通过"
```

## 检查清单

### Python SDK
- [ ] 可以从PyPI安装
- [ ] 可以正常导入
- [ ] 基本功能可用
- [ ] PyPI页面显示正确
- [ ] 文档链接正确

### Node.js SDK
- [ ] 可以从npm安装
- [ ] 可以正常导入（CommonJS和ES Modules）
- [ ] TypeScript类型定义可用
- [ ] 基本功能可用
- [ ] npm页面显示正确
- [ ] 文档链接正确

## 问题排查

### 如果安装失败
1. 检查网络连接
2. 检查PyPI/npm服务状态
3. 检查包名是否正确
4. 检查版本号是否存在

### 如果导入失败
1. 检查安装是否成功
2. 检查Python/Node.js版本
3. 检查依赖是否安装完整

### 如果功能测试失败
1. 检查API密钥是否正确
2. 检查API URL是否正确
3. 检查网络连接
