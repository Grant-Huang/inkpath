import { test, expect } from '@playwright/test';

/**
 * 故事列表页面功能测试
 */
test.describe('故事列表页面', () => {
  test.beforeEach(async ({ page }) => {
    // 访问故事列表页面
    await page.goto('/index.html');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test('应该显示页面标题和描述', async ({ page }) => {
    // 检查页面标题（使用更精确的选择器，选择故事列表视图中的h1）
    const storiesView = page.locator('#view-stories');
    await expect(storiesView.locator('h1')).toContainText('故事库');
    
    // 检查描述文本
    await expect(page.locator('text=AI 协作续写正在进行中的故事')).toBeVisible();
  });

  test('应该显示故事卡片列表', async ({ page }) => {
    // 检查至少有一个故事卡片
    const storyCards = page.locator('[onclick*="selectStory"]');
    await expect(storyCards).toHaveCount(3);
    
    // 检查第一个故事卡片的内容
    const firstCard = storyCards.first();
    await expect(firstCard.locator('text=星尘行人')).toBeVisible();
    await expect(firstCard.locator('text=科幻')).toBeVisible();
    await expect(firstCard.locator('text=一个星际殖民者在未知星球上的故事')).toBeVisible();
  });

  test('应该显示故事卡片的统计信息', async ({ page }) => {
    const firstCard = page.locator('[onclick*="selectStory"]').first();
    
    // 检查分支数和Bot数
    await expect(firstCard.locator('text=/\\d+ 条分支/')).toBeVisible();
    await expect(firstCard.locator('text=/\\d+ 个 Bot/')).toBeVisible();
  });

  test('应该能够点击故事卡片进入详情页', async ({ page }) => {
    // 点击第一个故事卡片
    await page.locator('[onclick*="selectStory"]').first().click();
    
    // 检查是否切换到阅读视图
    await expect(page.locator('#view-reading')).toBeVisible();
    await expect(page.locator('#view-stories')).not.toBeVisible();
  });

  test('应该显示创建新故事按钮', async ({ page }) => {
    const createButton = page.locator('text=+ 创建新故事');
    await expect(createButton).toBeVisible();
  });

  test('应该能够打开创建故事模态框', async ({ page }) => {
    // 点击创建新故事按钮
    await page.locator('text=+ 创建新故事').click();
    
    // 检查模态框是否显示
    const modal = page.locator('#modal-create-story');
    await expect(modal).toBeVisible();
    
    // 检查模态框标题
    await expect(modal.locator('h2')).toContainText('创建新故事');
  });

  test('创建故事模态框应该包含所有必需字段', async ({ page }) => {
    // 打开模态框
    await page.locator('text=+ 创建新故事').click();
    await page.waitForSelector('#modal-create-story');
    
    const modal = page.locator('#modal-create-story');
    
    // 检查故事标题输入框
    await expect(modal.locator('#story-title')).toBeVisible();
    await expect(modal.locator('label:has-text("故事标题")')).toBeVisible();
    
    // 检查语言选择框
    await expect(modal.locator('#story-language')).toBeVisible();
    
    // 检查文件上传区域
    await expect(modal.locator('text=上传故事包')).toBeVisible();
    // 文件上传输入框是hidden的（通过按钮触发），检查它存在即可
    await expect(modal.locator('#story-pack-files')).toHaveCount(1);
    
    // 检查写作风格规范输入框
    await expect(modal.locator('#story-style')).toBeVisible();
  });

  test('应该能够关闭创建故事模态框', async ({ page }) => {
    // 打开模态框
    await page.locator('text=+ 创建新故事').click();
    await page.waitForSelector('#modal-create-story');
    
    // 点击取消按钮
    await page.locator('#modal-create-story button:has-text("取消")').click();
    
    // 检查模态框是否隐藏
    await expect(page.locator('#modal-create-story')).not.toBeVisible();
  });

  test('顶部导航栏应该显示正确', async ({ page }) => {
    // 检查Logo
    await expect(page.locator('text=墨径')).toBeVisible();
    await expect(page.locator('text=InkPath')).toBeVisible();
    
    // 检查导航按钮
    await expect(page.locator('#nav-stories')).toBeVisible();
    await expect(page.locator('#nav-stories')).toContainText('故事库');
    
    // 检查活跃故事数
    await expect(page.locator('text=/\\d+ 个活跃故事/')).toBeVisible();
    
    // 检查用户头像
    await expect(page.locator('.w-7, .w-8').last()).toBeVisible();
  });

  test('应该能够通过导航按钮切换视图', async ({ page }) => {
    // 点击故事库按钮（应该已经在故事库页面）
    await page.locator('#nav-stories').click();
    await expect(page.locator('#view-stories')).toBeVisible();
    
    // 如果有阅读视图按钮，测试切换
    const readingNav = page.locator('#nav-reading');
    if (await readingNav.isVisible()) {
      await readingNav.click();
      await expect(page.locator('#view-reading')).toBeVisible();
    }
  });
});
