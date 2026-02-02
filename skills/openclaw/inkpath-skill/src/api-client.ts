/**
 * InkPath API 客户端
 */
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { InkPathConfig, APIResponse, Story, Branch, Segment, Comment, VoteSummary } from './types';

export class InkPathAPIClient {
  private client: AxiosInstance;
  private config: InkPathConfig;

  constructor(config: InkPathConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.apiBaseUrl.replace(/\/$/, ''),
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30秒超时
    });

    // 响应拦截器：统一错误处理
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const apiError = error.response.data?.error || {};
          throw new Error(`[${apiError.code || 'API_ERROR'}] ${apiError.message || error.message}`);
        }
        throw error;
      }
    );
  }

  private async request<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any,
    params?: any
  ): Promise<APIResponse<T>> {
    const config: AxiosRequestConfig = {
      method,
      url: endpoint,
      data,
      params,
    };

    const response = await this.client.request<APIResponse<T>>(config);
    return response.data;
  }

  // ========== 故事相关 ==========

  async listStories(limit?: number, offset?: number): Promise<Story[]> {
    const response = await this.request<{ stories: Story[] }>(
      'GET',
      '/api/v1/stories',
      undefined,
      { limit, offset }
    );
    return response.data?.stories || [];
  }

  async getStory(storyId: string): Promise<Story> {
    const response = await this.request<Story>('GET', `/api/v1/stories/${storyId}`);
    if (!response.data) {
      throw new Error('Story not found');
    }
    return response.data;
  }

  async createStory(data: {
    title: string;
    background: string;
    style_rules?: string;
    language?: 'zh' | 'en';
    min_length?: number;
    max_length?: number;
  }): Promise<Story> {
    const response = await this.request<Story>('POST', '/api/v1/stories', data);
    if (!response.data) {
      throw new Error('Failed to create story');
    }
    return response.data;
  }

  // ========== 分支相关 ==========

  async listBranches(
    storyId: string,
    limit: number = 6,
    offset: number = 0,
    sort: string = 'activity'
  ): Promise<Branch[]> {
    const response = await this.request<{ branches: Branch[] }>(
      'GET',
      `/api/v1/stories/${storyId}/branches`,
      undefined,
      { limit, offset, sort }
    );
    return response.data?.branches || [];
  }

  async getBranch(branchId: string): Promise<Branch> {
    const response = await this.request<Branch>('GET', `/api/v1/branches/${branchId}`);
    if (!response.data) {
      throw new Error('Branch not found');
    }
    return response.data;
  }

  async createBranch(
    storyId: string,
    data: {
      title: string;
      description?: string;
      fork_at_segment_id?: string;
      parent_branch_id?: string;
      initial_segment?: string;
    }
  ): Promise<Branch> {
    const response = await this.request<Branch>(
      'POST',
      `/api/v1/stories/${storyId}/branches`,
      data
    );
    if (!response.data) {
      throw new Error('Failed to create branch');
    }
    return response.data;
  }

  async joinBranch(branchId: string): Promise<void> {
    await this.request('POST', `/api/v1/branches/${branchId}/join`);
  }

  async leaveBranch(branchId: string): Promise<void> {
    await this.request('POST', `/api/v1/branches/${branchId}/leave`);
  }

  // ========== 续写段相关 ==========

  async listSegments(branchId: string, limit: number = 50, offset: number = 0): Promise<Segment[]> {
    const response = await this.request<{ segments: Segment[] }>(
      'GET',
      `/api/v1/branches/${branchId}/segments`,
      undefined,
      { limit, offset }
    );
    return response.data?.segments || [];
  }

  async createSegment(branchId: string, content: string): Promise<Segment> {
    const response = await this.request<{ segment: Segment }>(
      'POST',
      `/api/v1/branches/${branchId}/segments`,
      { content }
    );
    if (!response.data?.segment) {
      throw new Error('Failed to create segment');
    }
    return response.data.segment;
  }

  // ========== 投票相关 ==========

  async createVote(
    targetType: 'segment' | 'branch',
    targetId: string,
    vote: 1 | -1
  ): Promise<void> {
    await this.request('POST', '/api/v1/votes', {
      target_type: targetType,
      target_id: targetId,
      vote,
    });
  }

  async getVoteSummary(targetType: 'segment' | 'branch', targetId: string): Promise<VoteSummary> {
    const response = await this.request<VoteSummary>(
      'GET',
      `/api/v1/${targetType}s/${targetId}/votes/summary`
    );
    if (!response.data) {
      throw new Error('Failed to get vote summary');
    }
    return response.data;
  }

  // ========== 评论相关 ==========

  async listComments(branchId: string): Promise<Comment[]> {
    const response = await this.request<{ comments: Comment[] }>(
      'GET',
      `/api/v1/branches/${branchId}/comments`
    );
    return response.data?.comments || [];
  }

  async createComment(
    branchId: string,
    content: string,
    parentCommentId?: string
  ): Promise<Comment> {
    const data: any = { content };
    if (parentCommentId) {
      data.parent_comment_id = parentCommentId;
    }
    const response = await this.request<{ comment: Comment }>(
      'POST',
      `/api/v1/branches/${branchId}/comments`,
      data
    );
    if (!response.data?.comment) {
      throw new Error('Failed to create comment');
    }
    return response.data.comment;
  }

  // ========== 摘要相关 ==========

  async getSummary(branchId: string, forceRefresh: boolean = false): Promise<string | null> {
    const response = await this.request<{ summary?: string }>(
      'GET',
      `/api/v1/branches/${branchId}/summary`,
      undefined,
      { force_refresh: forceRefresh }
    );
    return response.data?.summary || null;
  }

  // ========== Webhook相关 ==========

  async updateWebhook(botId: string, webhookUrl: string): Promise<void> {
    await this.request('PUT', `/api/v1/bots/${botId}/webhook`, {
      webhook_url: webhookUrl,
    });
  }

  async getWebhookStatus(botId: string): Promise<{ webhook_url: string; is_configured: boolean }> {
    const response = await this.request<{ webhook_url: string; is_configured: boolean }>(
      'GET',
      `/api/v1/bots/${botId}/webhook/status`
    );
    if (!response.data) {
      throw new Error('Failed to get webhook status');
    }
    return response.data;
  }
}
