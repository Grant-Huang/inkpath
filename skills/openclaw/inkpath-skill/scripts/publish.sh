#!/bin/bash
# InkPath OpenClaw Skill 发布脚本

set -e

echo "=== InkPath OpenClaw Skill 发布脚本 ==="
echo ""

# 检查是否在正确的目录
if [ ! -f "package.json" ]; then
    echo "错误: 请在 inkpath-skill 目录下运行此脚本"
    exit 1
fi

# 清理旧构建
echo "1. 清理旧构建..."
rm -rf dist/
echo "✓ 清理完成"
echo ""

# 构建
echo "2. 构建..."
npm run build
echo "✓ 构建完成"
echo ""

# 列出构建的文件
echo "3. 构建的文件:"
ls -lh dist/
echo ""

echo "=== 构建完成 ==="
echo ""
echo "下一步:"
echo "  1. 提交到 GitHub"
echo "  2. 在 OpenClaw Skill 市场提交 Skill"
echo "  3. 或发布到 npm: npm publish --access public"
echo ""
