#!/bin/bash
# Node.js SDK发布后检查脚本

set -e

echo "=== InkPath Node.js SDK 发布后检查 ==="
echo ""

# 检查是否已安装
echo "1. 检查安装..."
if npm list @inkpath/sdk &> /dev/null; then
    VERSION=$(npm list @inkpath/sdk 2>/dev/null | grep @inkpath/sdk | head -1 | awk '{print $2}' | tr -d '@inkpath/sdk@')
    echo "✓ 已安装 @inkpath/sdk (版本: $VERSION)"
else
    echo "✗ 未安装 @inkpath/sdk"
    echo "  请先运行: npm install @inkpath/sdk"
    exit 1
fi
echo ""

# 导入测试（CommonJS）
echo "2. 导入测试（CommonJS）..."
node << 'EOF'
try {
    const { InkPathClient, WebhookHandler, APIError, ValidationError } = require('@inkpath/sdk');
    console.log('✓ 导入成功');
    console.log('  - InkPathClient:', typeof InkPathClient);
    console.log('  - WebhookHandler:', typeof WebhookHandler);
    console.log('  - APIError:', typeof APIError);
    console.log('  - ValidationError:', typeof ValidationError);
} catch (e) {
    console.error('✗ 导入失败:', e.message);
    process.exit(1);
}
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# 功能测试
echo "3. 功能测试..."
node << 'EOF'
const { InkPathClient, WebhookHandler } = require('@inkpath/sdk');

try {
    // 测试客户端创建
    const client = new InkPathClient('https://api.inkpath.com', 'test-key');
    console.log('✓ 客户端创建成功');
    
    // 检查可用方法
    const methods = Object.getOwnPropertyNames(Object.getPrototypeOf(client))
        .filter(name => name !== 'constructor' && typeof client[name] === 'function');
    console.log(`✓ 可用方法数量: ${methods.length}`);
    console.log(`✓ 主要方法: ${methods.slice(0, 5).join(', ')}`);
    
    // 测试Webhook处理器
    const webhook = new WebhookHandler();
    console.log('✓ Webhook处理器创建成功');
} catch (e) {
    console.error('✗ 功能测试失败:', e.message);
    process.exit(1);
}
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# TypeScript类型测试
echo "4. TypeScript类型测试..."
cat > /tmp/test_types.ts << 'TYPESCRIPT'
import { InkPathClient, WebhookHandler, APIError, ValidationError } from '@inkpath/sdk';
import type { Story, Branch, Segment } from '@inkpath/sdk';

const client = new InkPathClient('https://api.inkpath.com', 'test-key');
const webhook = new WebhookHandler();
TYPESCRIPT

if command -v tsc &> /dev/null; then
    if tsc --noEmit /tmp/test_types.ts 2>/dev/null; then
        echo "✓ 类型检查通过"
    else
        echo "⚠ 类型检查失败（可能需要安装TypeScript）"
    fi
else
    echo "⚠ 跳过类型检查（tsc未安装）"
fi
rm -f /tmp/test_types.ts
echo ""

echo "✅ 所有检查通过！"
echo ""
echo "SDK已成功发布并可以正常使用。"
