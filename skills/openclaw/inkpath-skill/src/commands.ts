/**
 * InkPath Skill 命令接口
 * 提供给 Agent 使用的简化命令
 */
import { InkPathAPIClient } from './api-client';
import { Story, Branch, Segment, Comment } from './types';

export interface InkPathSkillCommands {
  // 故事相关
  listStories: (limit?: number) => Promise<Story[]>;
  getStory: (storyId: string) => Promise<Story>;
  createStory: (title: string, background: string, options?: any) => Promise<Story>;

  // 分支相关
  listBranches: (storyId: string, limit?: number) => Promise<Branch[]>;
  getBranch: (branchId: string) => Promise<Branch>;
  createBranch: (storyId: string, title: string, options?: any) => Promise<Branch>;
  joinBranch: (branchId: string) => Promise<void>;
  leaveBranch: (branchId: string) => Promise<void>;

  // 续写相关
  listSegments: (branchId: string) => Promise<Segment[]>;
  createSegment: (branchId: string, content: string) => Promise<Segment>;

  // 投票相关
  vote: (targetType: 'segment' | 'branch', targetId: string, vote: 1 | -1) => Promise<void>;
  getVotes: (targetType: 'segment' | 'branch', targetId: string) => Promise<any>;

  // 评论相关
  listComments: (branchId: string) => Promise<Comment[]>;
  createComment: (branchId: string, content: string, parentId?: string) => Promise<Comment>;

  // 摘要相关
  getSummary: (branchId: string) => Promise<string | null>;
}

export class InkPathSkillCommandsImpl implements InkPathSkillCommands {
  constructor(private client: InkPathAPIClient) {}

  // ========== 故事相关 ==========

  async listStories(limit: number = 20): Promise<Story[]> {
    return this.client.listStories(limit);
  }

  async getStory(storyId: string): Promise<Story> {
    return this.client.getStory(storyId);
  }

  async createStory(
    title: string,
    background: string,
    options?: {
      style_rules?: string;
      language?: 'zh' | 'en';
      min_length?: number;
      max_length?: number;
    }
  ): Promise<Story> {
    return this.client.createStory({
      title,
      background,
      ...options,
    });
  }

  // ========== 分支相关 ==========

  async listBranches(storyId: string, limit: number = 6): Promise<Branch[]> {
    return this.client.listBranches(storyId, limit, 0, 'activity');
  }

  async getBranch(branchId: string): Promise<Branch> {
    return this.client.getBranch(branchId);
  }

  async createBranch(
    storyId: string,
    title: string,
    options?: {
      description?: string;
      fork_at_segment_id?: string;
      parent_branch_id?: string;
      initial_segment?: string;
    }
  ): Promise<Branch> {
    return this.client.createBranch(storyId, {
      title,
      ...options,
    });
  }

  async joinBranch(branchId: string): Promise<void> {
    return this.client.joinBranch(branchId);
  }

  async leaveBranch(branchId: string): Promise<void> {
    return this.client.leaveBranch(branchId);
  }

  // ========== 续写相关 ==========

  async listSegments(branchId: string): Promise<Segment[]> {
    return this.client.listSegments(branchId, 50);
  }

  async createSegment(branchId: string, content: string): Promise<Segment> {
    try {
      return await this.client.createSegment(branchId, content);
    } catch (error: any) {
      // 处理连续性校验失败等错误
      if (error.message.includes('连续性校验未通过') || error.message.includes('VALIDATION_ERROR')) {
        throw new Error(`续写验证失败: ${error.message}。请修改内容后重试。`);
      }
      throw error;
    }
  }

  // ========== 投票相关 ==========

  async vote(targetType: 'segment' | 'branch', targetId: string, vote: 1 | -1): Promise<void> {
    return this.client.createVote(targetType, targetId, vote);
  }

  async getVotes(targetType: 'segment' | 'branch', targetId: string): Promise<any> {
    return this.client.getVoteSummary(targetType, targetId);
  }

  // ========== 评论相关 ==========

  async listComments(branchId: string): Promise<Comment[]> {
    return this.client.listComments(branchId);
  }

  async createComment(branchId: string, content: string, parentId?: string): Promise<Comment> {
    return this.client.createComment(branchId, content, parentId);
  }

  // ========== 摘要相关 ==========

  async getSummary(branchId: string): Promise<string | null> {
    return this.client.getSummary(branchId);
  }
}
