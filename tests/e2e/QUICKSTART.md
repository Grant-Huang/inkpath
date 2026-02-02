# Playwright E2E 测试快速启动指南

## 快速开始

### 1. 安装 Node.js 和 npm

确保已安装 Node.js (推荐 v18 或更高版本)：

```bash
node --version
npm --version
```

### 2. 安装依赖

```bash
# 在项目根目录执行
npm install
```

### 3. 安装 Playwright 浏览器

```bash
npx playwright install
```

### 4. 运行测试

```bash
# 运行所有测试
npm test

# 或使用 playwright 命令
npx playwright test
```

## 常用命令

```bash
# 运行特定测试文件
npx playwright test tests/e2e/test_stories_page.spec.ts

# 运行特定浏览器
npx playwright test --project=chromium

# UI 模式运行（推荐，可视化测试执行）
npx playwright test --ui

# 调试模式运行
npx playwright test --debug

# 查看测试报告
npm run report
# 或
npx playwright show-report
```

## 测试文件说明

| 测试文件 | 测试内容 |
|---------|---------|
| `test_stories_page.spec.ts` | 故事列表页面功能 |
| `test_reading_view.spec.ts` | 故事详情/阅读页面功能 |
| `test_interactions.spec.ts` | 交互功能（投票、讨论等） |
| `test_responsive.spec.ts` | 响应式设计 |

## 测试配置

测试配置在 `playwright.config.ts` 中，主要设置：

- **测试服务器**: 自动启动 `python -m http.server 8000` 在 `demo/` 目录
- **测试URL**: `http://localhost:8000/index.html`
- **浏览器**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari

## 故障排除

### 问题：测试无法连接到服务器

**解决方案**：
1. 确保 demo 目录存在且包含 `index.html`
2. 手动启动服务器：`cd demo && python -m http.server 8000`
3. 检查端口 8000 是否被占用

### 问题：浏览器未安装

**解决方案**：
```bash
npx playwright install
npx playwright install chromium  # 只安装 Chromium
```

### 问题：TypeScript 编译错误

**解决方案**：
1. 确保已安装依赖：`npm install`
2. 检查 `tsconfig.json` 配置
3. 确保使用 Node.js v18+

## 编写新测试

参考现有测试文件的结构：

```typescript
import { test, expect } from '@playwright/test';

test.describe('功能描述', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('networkidle');
  });

  test('测试用例描述', async ({ page }) => {
    // 测试代码
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

## CI/CD 集成

在 CI 环境中，测试会自动：
1. 安装依赖
2. 安装浏览器
3. 启动测试服务器
4. 运行测试
5. 生成报告

示例 GitHub Actions 配置：

```yaml
- name: Install dependencies
  run: npm install

- name: Install Playwright browsers
  run: npx playwright install --with-deps

- name: Run tests
  run: npx playwright test
```

## 更多信息

详细文档请查看 `tests/e2e/README.md`
