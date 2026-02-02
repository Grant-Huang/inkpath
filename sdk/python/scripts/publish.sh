#!/bin/bash
# InkPath Python SDK发布脚本

set -e

echo "=== InkPath Python SDK 发布脚本 ==="
echo ""

# 检查是否在正确的目录
if [ ! -f "setup.py" ]; then
    echo "错误: 请在 sdk/python 目录下运行此脚本"
    exit 1
fi

# 清理旧构建
echo "1. 清理旧构建..."
rm -rf build/ dist/ *.egg-info
echo "✓ 清理完成"
echo ""

# 构建分发包
echo "2. 构建分发包..."
python setup.py sdist bdist_wheel
echo "✓ 构建完成"
echo ""

# 列出构建的文件
echo "3. 构建的文件:"
ls -lh dist/
echo ""

# 检查分发包（需要安装twine）
if command -v twine &> /dev/null; then
    echo "4. 检查分发包..."
    twine check dist/*
    echo "✓ 检查完成"
    echo ""
else
    echo "4. 跳过检查（twine未安装，运行: pip install twine）"
    echo ""
fi

echo "=== 构建完成 ==="
echo ""
echo "下一步:"
echo "  测试发布: twine upload --repository testpypi dist/*"
echo "  正式发布: twine upload dist/*"
echo ""
echo "注意: 发布前请确保:"
echo "  - 版本号已更新"
echo "  - 所有测试通过"
echo "  - README和文档已更新"
