/**
 * Webhook 处理器
 * 处理来自 InkPath 的 Webhook 通知
 */
import { WebhookEvent } from './types';

export type WebhookEventHandler = (event: WebhookEvent) => void | Promise<void>;

export class WebhookHandler {
  private handlers: Map<string, WebhookEventHandler[]> = new Map();

  /**
   * 注册事件处理器
   */
  on(event: 'your_turn' | 'new_branch', handler: WebhookEventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  /**
   * 处理 Webhook 请求
   */
  async handle(event: WebhookEvent): Promise<void> {
    const handlers = this.handlers.get(event.event);
    if (!handlers || handlers.length === 0) {
      console.warn(`No handler registered for event: ${event.event}`);
      return;
    }

    // 执行所有注册的处理器
    for (const handler of handlers) {
      try {
        await handler(event);
      } catch (error) {
        console.error(`Error in webhook handler for ${event.event}:`, error);
        // 继续执行其他处理器，不中断
      }
    }
  }

  /**
   * 验证 Webhook 请求（可选，用于 HMAC 签名验证）
   */
  verifySignature(payload: string, signature: string, secret: string): boolean {
    // TODO: 实现 HMAC-SHA256 签名验证
    // 目前返回 true，实际使用时需要实现
    return true;
  }
}
