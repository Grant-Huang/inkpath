# E2E 前端功能测试

本目录包含使用 Playwright 编写的前端功能测试脚本，用于测试墨径 InkPath 平台的前端界面功能。

## 测试文件说明

- `test_stories_page.spec.ts` - 故事列表页面功能测试
  - 页面标题和描述显示
  - 故事卡片列表显示
  - 故事卡片统计信息
  - 创建新故事功能
  - 导航栏功能

- `test_reading_view.spec.ts` - 故事详情/阅读页面功能测试
  - 故事标题和元信息显示
  - 摘要卡片折叠/展开
  - 续写段列表显示
  - 投票功能
  - 分支树显示和选择
  - 参与者列表
  - 讨论区功能
  - 创建分支功能

- `test_interactions.spec.ts` - 交互功能测试
  - 投票操作和统计更新
  - 讨论区展开/折叠
  - 评论输入
  - 分支创建表单填写
  - 模态框交互

- `test_responsive.spec.ts` - 响应式设计测试
  - 桌面端布局
  - 移动端布局
  - 平板端布局
  - 不同屏幕尺寸下的界面表现

## 安装和运行

### 1. 安装依赖

```bash
# 安装 Node.js 依赖（Playwright）
npm install

# 安装 Playwright 浏览器
npx playwright install
```

### 2. 运行测试

```bash
# 运行所有 E2E 测试
npx playwright test

# 运行特定测试文件
npx playwright test tests/e2e/test_stories_page.spec.ts

# 运行特定浏览器
npx playwright test --project=chromium

# 以 UI 模式运行（交互式）
npx playwright test --ui

# 以调试模式运行
npx playwright test --debug
```

### 3. 查看测试报告

```bash
# 查看 HTML 测试报告
npx playwright show-report
```

## 测试配置

测试配置位于项目根目录的 `playwright.config.ts` 文件中。

默认配置：
- 测试服务器：`http://localhost:8000` (demo 目录)
- 支持的浏览器：Chromium, Firefox, WebKit
- 移动端测试：Pixel 5, iPhone 12

## 注意事项

1. 测试需要先启动 demo 服务器（通过 `playwright.config.ts` 中的 webServer 配置自动启动）
2. 测试基于 demo/index.html 文件，确保该文件存在且可访问
3. 部分测试可能需要等待 JavaScript 执行完成，已添加适当的等待机制
4. 响应式测试会测试多个屏幕尺寸，确保界面在不同设备上正常显示

## 测试覆盖范围

- ✅ 故事列表页面
- ✅ 故事详情/阅读页面
- ✅ 投票功能
- ✅ 讨论区功能
- ✅ 分支创建功能
- ✅ 模态框交互
- ✅ 响应式设计
- ✅ 导航功能

## 持续集成

在 CI/CD 环境中运行时，测试会自动：
- 安装 Playwright 浏览器
- 启动测试服务器
- 运行所有测试
- 生成测试报告
