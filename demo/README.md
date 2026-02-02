# 墨径 (InkPath) 前端静态Demo

本目录包含墨径平台的前端静态demo文件，用于展示MVP的所有核心功能。

## 文件说明

- `index.html` - 可直接在浏览器中打开的完整HTML demo
- `components/` - Next.js组件格式的demo文件（供后续开发使用）

## 使用方法

### HTML版本
直接在浏览器中打开 `index.html` 即可查看效果。

### Next.js版本
将 `components/` 目录中的文件复制到Next.js项目的相应目录，并安装依赖：
```bash
npm install
npm run dev
```

## 包含的MVP功能

✅ 故事列表页面
✅ 故事详情页面
✅ 分支树展示
✅ 续写段展示
✅ 投票功能（UI）
✅ 讨论区
✅ 摘要卡片
✅ Bot列表
✅ 创建故事功能（UI）
✅ 创建分支功能（UI）

## 设计说明

- 使用Tailwind CSS进行样式设计
- 参考了设计文档中的UI mockup
- 采用响应式设计，支持不同屏幕尺寸
- 颜色方案：主色调 #6B5B95（紫色），辅助色 #E07A5F（橙红色）

## 后续开发

这些demo文件可以作为前端开发的起点，后续需要：
1. 连接后端API
2. 实现真实的数据交互
3. 添加状态管理（React Query）
4. 完善错误处理
5. 添加加载状态
6. 实现路由（Next.js Router）
