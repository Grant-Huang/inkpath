#!/bin/bash
# Python SDK发布后检查脚本

set -e

echo "=== InkPath Python SDK 发布后检查 ==="
echo ""

# 检查是否已安装
echo "1. 检查安装..."
if pip show inkpath-sdk &> /dev/null; then
    VERSION=$(pip show inkpath-sdk | grep Version | awk '{print $2}')
    echo "✓ 已安装 inkpath-sdk (版本: $VERSION)"
else
    echo "✗ 未安装 inkpath-sdk"
    echo "  请先运行: pip install inkpath-sdk"
    exit 1
fi
echo ""

# 导入测试
echo "2. 导入测试..."
python << 'EOF'
try:
    from inkpath import InkPathClient, WebhookHandler, APIError, ValidationError
    print("✓ 导入成功")
    print("  - InkPathClient:", InkPathClient)
    print("  - WebhookHandler:", WebhookHandler)
    print("  - APIError:", APIError)
    print("  - ValidationError:", ValidationError)
except ImportError as e:
    print("✗ 导入失败:", e)
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# 功能测试
echo "3. 功能测试..."
python << 'EOF'
from inkpath import InkPathClient, WebhookHandler

# 测试客户端创建
try:
    client = InkPathClient('https://api.inkpath.com', 'test-key')
    print("✓ 客户端创建成功")
    
    # 检查可用方法
    methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
    print(f"✓ 可用方法数量: {len(methods)}")
    print(f"✓ 主要方法: {', '.join(methods[:5])}")
except Exception as e:
    print("✗ 客户端创建失败:", e)
    exit(1)

# 测试Webhook处理器
try:
    webhook = WebhookHandler()
    print("✓ Webhook处理器创建成功")
except Exception as e:
    print("✗ Webhook处理器创建失败:", e)
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

echo "✅ 所有检查通过！"
echo ""
echo "SDK已成功发布并可以正常使用。"
