# Next.js 组件格式 Demo

这些组件文件可以用于Next.js项目开发。

## 文件结构

```
components/
├── layout/
│   └── TopNav.tsx          # 顶部导航栏
├── stories/
│   ├── StoryList.tsx       # 故事列表页面
│   ├── ReadingView.tsx     # 阅读视图（故事详情）
│   └── SummaryCard.tsx     # 摘要卡片
├── branches/
│   └── BranchTree.tsx      # 分支树组件
├── segments/
│   └── SegmentCard.tsx    # 续写段卡片
├── discussion/
│   └── DiscussionPanel.tsx # 讨论区面板
└── pages/
    ├── StoriesPage.tsx     # 故事列表页面
    ├── StoryDetailPage.tsx # 故事详情页面
    └── App.tsx             # 主应用组件
```

## 使用方法

1. 将这些文件复制到你的Next.js项目的相应目录
2. 安装依赖：
```bash
npm install
```

3. 配置Tailwind CSS（如果还没有配置）：
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

4. 在 `app/layout.tsx` 或 `pages/_app.tsx` 中引入全局样式：
```tsx
import '../styles/globals.css'
```

5. 创建 `styles/globals.css`：
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

6. 添加字体（在 `app/layout.tsx` 或 `pages/_app.tsx`）：
```tsx
import { Playfair_Display } from 'next/font/google'

const playfair = Playfair_Display({ subsets: ['latin'] })
```

## 组件说明

### TopNav
顶部导航栏，包含Logo、导航按钮和用户信息。

### StoryList
故事列表页面，展示所有故事卡片，支持创建新故事。

### ReadingView
故事阅读视图，包含：
- 分支树
- 摘要卡片
- 续写段列表
- 讨论区
- Bot列表

### BranchTree
分支树组件，展示故事的所有分支，支持选择分支和创建新分支。

### SegmentCard
续写段卡片，展示每段续写的内容、作者、时间和投票功能。

### SummaryCard
摘要卡片，可折叠，展示分支的当前进展摘要。

### DiscussionPanel
讨论区面板，展示评论列表和发表评论功能。

## 后续开发

这些组件目前使用mock数据，后续需要：

1. **连接API**：使用React Query或SWR获取真实数据
2. **状态管理**：使用Context API或Zustand管理全局状态
3. **路由**：使用Next.js Router进行页面导航
4. **错误处理**：添加错误边界和加载状态
5. **类型定义**：完善TypeScript类型定义
6. **测试**：添加单元测试和集成测试

## 注意事项

- 所有组件都使用 `'use client'` 指令，因为包含交互功能
- 样式使用Tailwind CSS，颜色方案参考设计文档
- 组件设计遵循单一职责原则，便于维护和测试
