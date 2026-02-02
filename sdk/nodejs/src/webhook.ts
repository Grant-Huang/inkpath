/**
 * Webhook处理器
 */
import express, { Express, Request, Response } from 'express';
import { WebhookEvent } from './types';

export type WebhookHandlerFunction = (event: WebhookEvent) => void | Promise<void>;

export class WebhookHandler {
  private app: Express;
  private handlers: Map<string, WebhookHandlerFunction> = new Map();

  constructor(secret?: string) {
    this.app = express();
    this.app.use(express.json());
    this.setupRoutes();
  }

  private setupRoutes(): void {
    this.app.post('/webhook', async (req: Request, res: Response) => {
      try {
        const event: WebhookEvent = req.body;

        if (!event.event) {
          return res.status(400).json({ error: 'Missing event field' });
        }

        const handler = this.handlers.get(event.event);
        if (handler) {
          try {
            await handler(event);
            return res.json({ status: 'ok' });
          } catch (error: any) {
            console.error('Webhook handler error:', error);
            return res.status(500).json({ error: 'Handler error' });
          }
        } else {
          console.warn(`Unknown webhook event: ${event.event}`);
          return res.json({ status: 'ok' }); // 未知事件也返回200，避免重试
        }
      } catch (error: any) {
        console.error('Webhook processing error:', error);
        return res.status(500).json({ error: 'Internal error' });
      }
    });
  }

  onYourTurn(handler: WebhookHandlerFunction): void {
    this.handlers.set('your_turn', handler);
  }

  onNewBranch(handler: WebhookHandlerFunction): void {
    this.handlers.set('new_branch', handler);
  }

  run(host: string = '0.0.0.0', port: number = 8080, callback?: () => void): void {
    this.app.listen(port, host, () => {
      console.log(`Webhook server running on ${host}:${port}`);
      if (callback) callback();
    });
  }

  getApp(): Express {
    return this.app;
  }
}
