#!/bin/bash
# GitHub 仓库设置脚本

set -e

echo "🚀 InkPath GitHub 仓库设置"
echo "=========================="
echo ""

# 检查是否已有远程仓库
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ 已配置远程仓库:"
    git remote -v
    echo ""
    read -p "是否要更新远程仓库地址? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入新的 GitHub 仓库地址: " repo_url
        git remote set-url origin "$repo_url"
        echo "✅ 远程仓库地址已更新"
    fi
else
    echo "📝 请提供 GitHub 仓库地址"
    echo ""
    echo "格式示例："
    echo "  HTTPS: https://github.com/username/inkpath.git"
    echo "  SSH:   git@github.com:username/inkpath.git"
    echo ""
    read -p "请输入 GitHub 仓库地址: " repo_url
    
    if [ -z "$repo_url" ]; then
        echo "❌ 仓库地址不能为空"
        exit 1
    fi
    
    git remote add origin "$repo_url"
    echo "✅ 远程仓库已添加: $repo_url"
fi

echo ""
echo "📤 推送到 GitHub..."
echo ""

# 检查当前分支
current_branch=$(git branch --show-current)
echo "当前分支: $current_branch"

# 推送代码
if git push -u origin "$current_branch" 2>&1; then
    echo ""
    echo "✅ 代码已成功推送到 GitHub!"
    echo ""
    echo "🔗 仓库地址: $(git remote get-url origin)"
else
    echo ""
    echo "❌ 推送失败，可能的原因："
    echo "   1. 仓库地址不正确"
    echo "   2. 没有推送权限"
    echo "   3. 需要先创建 GitHub 仓库"
    echo ""
    echo "💡 如果还没有创建 GitHub 仓库，请："
    echo "   1. 访问 https://github.com/new"
    echo "   2. 创建新仓库（不要初始化 README）"
    echo "   3. 然后重新运行此脚本"
    exit 1
fi
