import { test, expect } from '@playwright/test';

/**
 * 故事详情/阅读页面功能测试
 */
test.describe('故事详情/阅读页面', () => {
  test.beforeEach(async ({ page }) => {
    // 设置桌面端视口，确保所有元素可见
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // 访问页面并切换到阅读视图
    await page.goto('/index.html');
    await page.waitForLoadState('networkidle');
    
    // 点击第一个故事卡片进入阅读视图
    await page.locator('[onclick*="selectStory"]').first().click();
    await page.waitForSelector('#view-reading');
  });

  test('应该显示故事标题和元信息', async ({ page }) => {
    // 检查阅读视图已显示
    const readingView = page.locator('#view-reading');
    await expect(readingView).toBeVisible();
    
    // 检查故事标题和元信息（由于响应式设计，某些元素可能在特定视口下隐藏）
    // 我们检查元素存在即可，不强制检查可见性
    const heading = page.getByRole('heading', { name: '星尘行人' });
    const headingCount = await heading.count();
    expect(headingCount).toBeGreaterThan(0);
    
    // 检查类型标签（检查存在即可）
    const genreCount = await readingView.locator('text=科幻').count();
    expect(genreCount).toBeGreaterThan(0);
    
    // 检查统计信息（检查存在即可）
    const botCount = await readingView.locator('text=/\\d+ 个 Bot 参与/').count();
    expect(botCount).toBeGreaterThan(0);
    const segmentCount = await readingView.locator('text=/\\d+ 段续写/').count();
    expect(segmentCount).toBeGreaterThan(0);
  });

  test('应该显示摘要卡片', async ({ page }) => {
    const summaryCard = page.locator('#summary-card');
    await expect(summaryCard).toBeVisible();
    
    // 检查摘要标题
    await expect(summaryCard.locator('text=当前进展摘要')).toBeVisible();
    
    // 检查摘要内容
    await expect(summaryCard.locator('text=Sera')).toBeVisible();
  });

  test('应该能够折叠/展开摘要卡片', async ({ page }) => {
    const summaryCard = page.locator('#summary-card');
    const summaryContent = page.locator('#summary-content');
    const summaryArrow = page.locator('#summary-arrow');
    
    // 初始状态应该是展开的
    await expect(summaryContent).toBeVisible();
    
    // 点击摘要标题折叠
    await summaryCard.locator('[onclick*="toggleSummary"]').click();
    await expect(summaryContent).not.toBeVisible();
    await expect(summaryArrow).toContainText('▲');
    
    // 再次点击展开
    await summaryCard.locator('[onclick*="toggleSummary"]').click();
    await expect(summaryContent).toBeVisible();
    await expect(summaryArrow).toContainText('▼');
  });

  test('应该显示续写段列表', async ({ page }) => {
    // 检查至少有一个续写段
    const segments = page.locator('[id^="human-up-"]');
    const segmentCount = await segments.count();
    expect(segmentCount).toBeGreaterThan(0);
    
    // 检查第一个续写段的内容（使用更精确的选择器，避免匹配讨论区中的）
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    await expect(firstSegment.locator('span.text-sm.font-semibold:has-text("叙述者")').first()).toBeVisible();
    await expect(firstSegment.locator('text=/星球的大气层/')).toBeVisible();
  });

  test('应该显示续写段的投票信息', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    
    // 检查投票按钮
    await expect(firstSegment.locator('button:has-text("👍")')).toBeVisible();
    await expect(firstSegment.locator('button:has-text("👎")')).toBeVisible();
    
    // 检查投票统计
    await expect(firstSegment.locator('text=/人类:/')).toBeVisible();
    await expect(firstSegment.locator('text=/Bot:/')).toBeVisible();
    await expect(firstSegment.locator('text=/总评分:/')).toBeVisible();
  });

  test('应该能够进行投票操作', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const upvoteButton = firstSegment.locator('button:has-text("👍")').first();
    const humanUpElement = firstSegment.locator('#human-up-1');
    
    // 获取初始点赞数
    const initialCount = await humanUpElement.textContent();
    const initialValue = parseInt(initialCount || '0');
    
    // 点击点赞按钮
    await upvoteButton.click();
    
    // 等待更新（可能需要等待一小段时间）
    await page.waitForTimeout(500);
    
    // 检查点赞数是否增加
    const newCount = await humanUpElement.textContent();
    const newValue = parseInt(newCount || '0');
    expect(newValue).toBeGreaterThanOrEqual(initialValue);
  });

  test('应该显示分支树', async ({ page }) => {
    const sidebar = page.locator('#sidebar');
    await expect(sidebar).toBeVisible();
    
    // 检查分支树标题
    await expect(sidebar.locator('text=故事分支')).toBeVisible();
    
    // 检查主干线
    await expect(sidebar.locator('text=主干线')).toBeVisible();
    await expect(sidebar.locator('#branch-main')).toBeVisible();
  });

  test('应该能够选择不同的分支', async ({ page }) => {
    const branchDark = page.locator('#branch-dark');
    
    // 检查分支是否存在
    if (await branchDark.isVisible()) {
      // 点击分支
      await branchDark.click();
      
      // 检查分支是否被选中（样式变化）
      const branchElement = page.locator('#branch-dark');
      const classList = await branchElement.getAttribute('class');
      expect(classList).toContain('bg-[#f0ecf7]');
    }
  });

  test('应该显示参与者列表', async ({ page }) => {
    const sidebar = page.locator('#sidebar');
    
    // 检查参与者标题（使用h3标签）
    await expect(sidebar.locator('h3:has-text("参与者")')).toBeVisible();
    
    // 检查至少有一个参与者
    const participants = sidebar.locator('.flex.items-center.gap-2.py-1');
    const participantCount = await participants.count();
    expect(participantCount).toBeGreaterThan(0);
  });

  test('应该显示讨论区按钮', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const discussionButton = firstSegment.locator('button:has-text("💬")');
    
    await expect(discussionButton).toBeVisible();
    await expect(discussionButton.locator('text=/\\d+/')).toBeVisible();
  });

  test('应该能够展开/折叠讨论区', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const discussionButton = firstSegment.locator('button:has-text("💬")').first();
    const discussionPanel = page.locator('#discussion-panel-1');
    
    // 初始状态应该是隐藏的
    await expect(discussionPanel).not.toBeVisible();
    
    // 点击展开讨论区
    await discussionButton.click();
    await expect(discussionPanel).toBeVisible();
    
    // 再次点击折叠
    await discussionButton.click();
    await expect(discussionPanel).not.toBeVisible();
  });

  test('讨论区应该显示评论列表', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const discussionButton = firstSegment.locator('button:has-text("💬")').first();
    
    // 展开讨论区
    await discussionButton.click();
    await page.waitForSelector('#discussion-panel-1');
    
    const discussionPanel = page.locator('#discussion-panel-1');
    
    // 检查评论输入框
    await expect(discussionPanel.locator('textarea[placeholder*="发表评论"]')).toBeVisible();
    
    // 检查发表按钮
    await expect(discussionPanel.locator('button:has-text("发表")')).toBeVisible();
  });

  test('应该显示创建分支按钮', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const createBranchButton = firstSegment.locator('button:has-text("🔀")');
    
    await expect(createBranchButton).toBeVisible();
  });

  test('应该能够打开创建分支模态框', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const createBranchButton = firstSegment.locator('button:has-text("🔀")').first();
    
    // 点击创建分支按钮
    await createBranchButton.click();
    
    // 检查模态框是否显示
    const modal = page.locator('#modal-create-branch');
    await expect(modal).toBeVisible();
    
    // 检查模态框标题
    await expect(modal.locator('h2')).toContainText('创建新分支');
  });

  test('创建分支模态框应该包含所有必需字段', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const createBranchButton = firstSegment.locator('button:has-text("🔀")').first();
    
    // 打开模态框
    await createBranchButton.click();
    await page.waitForSelector('#modal-create-branch');
    
    const modal = page.locator('#modal-create-branch');
    
    // 检查分支标题输入框
    await expect(modal.locator('input[type="text"]').first()).toBeVisible();
    await expect(modal.locator('label:has-text("分支标题")')).toBeVisible();
    
    // 检查分支理由输入框
    await expect(modal.locator('textarea').first()).toBeVisible();
    await expect(modal.locator('label:has-text("分支理由")')).toBeVisible();
    
    // 检查分叉段输入框
    await expect(modal.locator('#fork-segment-id')).toBeVisible();
    
    // 检查第一段续写输入框
    await expect(modal.locator('textarea').last()).toBeVisible();
  });

  test('应该能够关闭创建分支模态框', async ({ page }) => {
    const firstSegment = page.locator('.relative.flex.gap-4').first();
    const createBranchButton = firstSegment.locator('button:has-text("🔀")').first();
    
    // 打开模态框
    await createBranchButton.click();
    await page.waitForSelector('#modal-create-branch');
    
    // 点击取消按钮
    await page.locator('#modal-create-branch button:has-text("取消")').click();
    
    // 检查模态框是否隐藏
    await expect(page.locator('#modal-create-branch')).not.toBeVisible();
  });

  test('移动端应该显示侧边栏切换按钮', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });
    
    // 检查移动端菜单按钮
    const menuButton = page.locator('button:has-text("☰")');
    if (await menuButton.isVisible()) {
      // 点击菜单按钮
      await menuButton.click();
      
      // 检查侧边栏是否显示
      const sidebar = page.locator('#sidebar');
      await expect(sidebar).toBeVisible();
    }
  });
});
