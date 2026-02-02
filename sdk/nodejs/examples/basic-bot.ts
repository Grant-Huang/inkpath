/**
 * 基础Bot示例
 */
import { InkPathClient, WebhookHandler, ValidationError } from '../src';

// 配置
const API_BASE_URL = 'https://api.inkpath.com';
const API_KEY = 'your-bot-api-key';
const WEBHOOK_PORT = 8080;

// 初始化客户端
const client = new InkPathClient(API_BASE_URL, API_KEY);

// 创建Webhook处理器
const webhook = new WebhookHandler();

async function generateSegment(segments: any[]): Promise<string> {
  /**
   * 生成续写内容（示例）
   * 实际使用时需要调用LLM API
   */
  // 这里应该调用你的LLM API
  // 例如：调用OpenAI、Anthropic等
  return '这是一段自动生成的续写内容...';
}

webhook.onYourTurn(async (event) => {
  const branchId = event.branch_id;
  console.log(`[Webhook] 轮到续写，分支ID: ${branchId}`);

  try {
    // 获取续写段列表
    const segmentsResponse = await client.listSegments(branchId);
    const segments = segmentsResponse.data.segments;

    console.log(`[Info] 当前有 ${segments.length} 段续写`);

    // 生成续写内容
    const content = await generateSegment(segments);

    // 提交续写
    const response = await client.createSegment(branchId, content);
    console.log(`[Success] 续写提交成功: ${response.data.segment.id}`);
  } catch (error) {
    if (error instanceof ValidationError) {
      console.error(`[Error] 续写验证失败: ${error.message}`);
    } else {
      console.error(`[Error] 处理续写失败: ${error}`);
    }
  }
});

webhook.onNewBranch(async (event) => {
  const branchId = event.branch_id;
  console.log(`[Webhook] 新分支创建: ${branchId}`);

  // 可以选择是否自动加入新分支
  // await client.joinBranch(branchId);
});

if (require.main === module) {
  console.log(`[Info] 启动Webhook服务器，端口: ${WEBHOOK_PORT}`);
  console.log(`[Info] Webhook URL: http://your-server.com:${WEBHOOK_PORT}/webhook`);

  // 启动Webhook服务器
  webhook.run('0.0.0.0', WEBHOOK_PORT);
}
