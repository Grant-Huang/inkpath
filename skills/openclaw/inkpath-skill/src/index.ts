/**
 * InkPath OpenClaw Skill
 * 
 * 提供给 OpenClaw Agent 使用的 InkPath 集成 Skill
 */
import { InkPathAPIClient } from './api-client';
import { InkPathSkillCommands, InkPathSkillCommandsImpl } from './commands';
import { WebhookHandler } from './webhook-handler';
import { InkPathConfig } from './types';

export interface InkPathSkill {
  client: InkPathAPIClient;
  commands: InkPathSkillCommands;
  webhook: WebhookHandler;
}

/**
 * 创建 InkPath Skill 实例
 */
export function createInkPathSkill(config: InkPathConfig): InkPathSkill {
  const client = new InkPathAPIClient(config);
  const commands = new InkPathSkillCommandsImpl(client);
  const webhook = new WebhookHandler();

  return {
    client,
    commands,
    webhook,
  };
}

/**
 * 默认导出
 */
export default createInkPathSkill;

// 导出类型和类
export { InkPathAPIClient } from './api-client';
export { InkPathSkillCommands, InkPathSkillCommandsImpl } from './commands';
export { WebhookHandler } from './webhook-handler';
export * from './types';
