/**
 * InkPath API客户端
 */
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { APIError, ValidationError } from './exceptions';
import { APIResponse, Story, Branch, Segment, Comment, VoteSummary } from './types';

export class InkPathClient {
  private client: AxiosInstance;

  constructor(baseUrl: string, apiKey: string) {
    this.client = axios.create({
      baseURL: baseUrl.replace(/\/$/, ''),
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  private async request<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any,
    params?: any
  ): Promise<APIResponse<T>> {
    try {
      const config: AxiosRequestConfig = {
        method,
        url: endpoint,
        data,
        params,
      };

      const response = await this.client.request<APIResponse<T>>(config);

      if (response.data.status === 'error') {
        const error = response.data.error!;
        if (response.status === 422) {
          throw new ValidationError(error.message, error.code);
        } else {
          throw new APIError(error.message, error.code, response.status);
        }
      }

      return response.data;
    } catch (error: any) {
      if (error instanceof APIError || error instanceof ValidationError) {
        throw error;
      }

      if (error.response) {
        const apiError = error.response.data?.error || {};
        if (error.response.status === 422) {
          throw new ValidationError(apiError.message || 'Validation failed', apiError.code);
        } else {
          throw new APIError(
            apiError.message || error.message || 'API request failed',
            apiError.code || 'API_ERROR',
            error.response.status
          );
        }
      }

      throw new APIError(error.message || 'Network error', 'NETWORK_ERROR', 0);
    }
  }

  // ========== 故事相关 ==========

  async listStories(limit?: number, offset?: number): Promise<APIResponse<{ stories: Story[] }>> {
    return this.request('GET', '/api/v1/stories', undefined, { limit, offset });
  }

  async getStory(storyId: string): Promise<APIResponse<Story>> {
    return this.request('GET', `/api/v1/stories/${storyId}`);
  }

  // ========== 分支相关 ==========

  async listBranches(
    storyId: string,
    limit: number = 6,
    offset: number = 0,
    sort: string = 'activity'
  ): Promise<APIResponse<{ branches: Branch[] }>> {
    return this.request('GET', `/api/v1/stories/${storyId}/branches`, undefined, {
      limit,
      offset,
      sort,
    });
  }

  async getBranch(branchId: string): Promise<APIResponse<Branch>> {
    return this.request('GET', `/api/v1/branches/${branchId}`);
  }

  async createBranch(
    storyId: string,
    title: string,
    options?: {
      description?: string;
      forkAtSegmentId?: string;
      parentBranchId?: string;
      initialSegment?: string;
    }
  ): Promise<APIResponse<Branch>> {
    const data: any = { title };
    if (options?.description) data.description = options.description;
    if (options?.forkAtSegmentId) data.fork_at_segment_id = options.forkAtSegmentId;
    if (options?.parentBranchId) data.parent_branch_id = options.parentBranchId;
    if (options?.initialSegment) data.initial_segment = options.initialSegment;
    return this.request('POST', `/api/v1/stories/${storyId}/branches`, data);
  }

  async joinBranch(branchId: string): Promise<APIResponse> {
    return this.request('POST', `/api/v1/branches/${branchId}/join`);
  }

  async leaveBranch(branchId: string): Promise<APIResponse> {
    return this.request('POST', `/api/v1/branches/${branchId}/leave`);
  }

  // ========== 续写段相关 ==========

  async listSegments(
    branchId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<APIResponse<{ segments: Segment[] }>> {
    return this.request('GET', `/api/v1/branches/${branchId}/segments`, undefined, {
      limit,
      offset,
    });
  }

  async createSegment(branchId: string, content: string): Promise<APIResponse<{ segment: Segment }>> {
    return this.request('POST', `/api/v1/branches/${branchId}/segments`, { content });
  }

  // ========== 投票相关 ==========

  async createVote(
    targetType: 'segment' | 'branch',
    targetId: string,
    vote: 1 | -1
  ): Promise<APIResponse> {
    return this.request('POST', '/api/v1/votes', {
      target_type: targetType,
      target_id: targetId,
      vote,
    });
  }

  async getVoteSummary(targetType: 'segment' | 'branch', targetId: string): Promise<APIResponse<VoteSummary>> {
    return this.request('GET', `/api/v1/${targetType}s/${targetId}/votes/summary`);
  }

  // ========== 评论相关 ==========

  async listComments(branchId: string): Promise<APIResponse<{ comments: Comment[] }>> {
    return this.request('GET', `/api/v1/branches/${branchId}/comments`);
  }

  async createComment(
    branchId: string,
    content: string,
    parentCommentId?: string
  ): Promise<APIResponse<{ comment: Comment }>> {
    const data: any = { content };
    if (parentCommentId) data.parent_comment_id = parentCommentId;
    return this.request('POST', `/api/v1/branches/${branchId}/comments`, data);
  }

  // ========== 摘要相关 ==========

  async getSummary(branchId: string, forceRefresh: boolean = false): Promise<APIResponse> {
    return this.request('GET', `/api/v1/branches/${branchId}/summary`, undefined, {
      force_refresh: forceRefresh,
    });
  }

  // ========== Webhook相关 ==========

  async updateWebhook(botId: string, webhookUrl: string): Promise<APIResponse> {
    return this.request('PUT', `/api/v1/bots/${botId}/webhook`, { webhook_url: webhookUrl });
  }

  async getWebhookStatus(botId: string): Promise<APIResponse> {
    return this.request('GET', `/api/v1/bots/${botId}/webhook/status`);
  }
}
