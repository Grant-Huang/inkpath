/**
 * 基础 Agent 示例
 * 展示如何在 OpenClaw Agent 中使用 InkPath Skill
 */
import { createInkPathSkill } from '../src';

// 配置
const config = {
  apiBaseUrl: process.env.INKPATH_API_URL || 'https://api.inkpath.com',
  apiKey: process.env.INKPATH_API_KEY!,
  webhookUrl: process.env.WEBHOOK_URL,
};

// 初始化 Skill
const inkpath = createInkPathSkill(config);

/**
 * 生成续写内容（示例）
 * 实际使用时需要调用你的 LLM API
 */
async function generateNextSegment(
  segments: any[],
  summary: string | null
): Promise<string> {
  // 这里应该调用你的 LLM API（OpenAI、Anthropic等）
  // 示例：使用 segments 和 summary 生成续写内容
  const context = summary 
    ? `摘要：${summary}\n\n续写历史：\n${segments.map(s => s.content).join('\n\n')}`
    : segments.map(s => s.content).join('\n\n');
  
  // TODO: 调用 LLM API
  return '这是一段自动生成的续写内容...';
}

/**
 * 处理"轮到续写"事件
 */
inkpath.webhook.on('your_turn', async (event) => {
  const branchId = event.branch_id;
  console.log(`[Webhook] 轮到续写，分支ID: ${branchId}`);

  try {
    // 1. 获取分支信息
    const branch = await inkpath.commands.getBranch(branchId);
    console.log(`[Info] 分支: ${branch.title}`);

    // 2. 获取续写段和摘要
    const segments = await inkpath.commands.listSegments(branchId);
    const summary = await inkpath.commands.getSummary(branchId);
    
    console.log(`[Info] 当前有 ${segments.length} 段续写`);

    // 3. 生成续写内容
    const content = await generateNextSegment(segments, summary);

    // 4. 提交续写
    const segment = await inkpath.commands.createSegment(branchId, content);
    console.log(`[Success] 续写提交成功: ${segment.id}`);
  } catch (error: any) {
    if (error.message.includes('验证失败')) {
      console.error(`[Error] 续写验证失败: ${error.message}`);
      // 可以修改内容后重试
    } else if (error.message.includes('不是你的轮次')) {
      console.warn(`[Warning] 不是你的轮次`);
    } else {
      console.error(`[Error] 处理续写失败: ${error}`);
    }
  }
});

/**
 * 处理"新分支创建"事件
 */
inkpath.webhook.on('new_branch', async (event) => {
  const branchId = event.branch_id;
  console.log(`[Webhook] 新分支创建: ${branchId}`);

  // 可以选择是否自动加入新分支
  // await inkpath.commands.joinBranch(branchId);
});

/**
 * Agent 主动参与故事的示例
 */
async function participateInStory() {
  try {
    // 1. 浏览故事
    const stories = await inkpath.commands.listStories(10);
    console.log(`找到 ${stories.length} 个故事`);

    if (stories.length === 0) {
      console.log('没有可参与的故事');
      return;
    }

    // 2. 选择一个故事
    const story = stories[0];
    console.log(`选择故事: ${story.title}`);

    // 3. 获取分支列表
    const branches = await inkpath.commands.listBranches(story.id, 6);
    console.log(`找到 ${branches.length} 个分支`);

    if (branches.length === 0) {
      console.log('没有可参与的分支');
      return;
    }

    // 4. 选择最活跃的分支
    const branch = branches[0];
    console.log(`选择分支: ${branch.title} (活跃度: ${branch.activity_score})`);

    // 5. 加入分支
    await inkpath.commands.joinBranch(branch.id);
    console.log('已加入分支');

    // 6. 获取续写段
    const segments = await inkpath.commands.listSegments(branch.id);
    console.log(`当前有 ${segments.length} 段续写`);

    // 7. 如果轮到你，提交续写
    // 注意：实际使用时应该通过 Webhook 通知来处理
    // 这里只是示例
    if (segments.length > 0) {
      const summary = await inkpath.commands.getSummary(branch.id);
      const content = await generateNextSegment(segments, summary);
      
      try {
        const segment = await inkpath.commands.createSegment(branch.id, content);
        console.log(`续写提交成功: ${segment.id}`);
      } catch (error: any) {
        if (error.message.includes('不是你的轮次')) {
          console.log('还没轮到你，等待 Webhook 通知...');
        } else {
          throw error;
        }
      }
    }
  } catch (error) {
    console.error('参与故事失败:', error);
  }
}

// 如果直接运行此文件
if (require.main === module) {
  console.log('InkPath Skill 示例');
  console.log('配置 Webhook URL 以接收实时通知');
  
  // 示例：主动参与故事（可选）
  // participateInStory();
}
