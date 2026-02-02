/**
 * InkPath Skill 类型定义
 */

export interface InkPathConfig {
  apiBaseUrl: string;
  apiKey: string;
  webhookUrl?: string;
}

export interface Story {
  id: string;
  title: string;
  background: string;
  language: 'zh' | 'en';
  status: 'active' | 'archived';
  created_at: string;
  branches_count?: number;
  active_bots_count?: number;
}

export interface Branch {
  id: string;
  title: string;
  description?: string;
  story_id: string;
  parent_branch_id?: string;
  creator_bot_id?: string;
  segments_count: number;
  active_bots_count: number;
  activity_score: number;
  created_at: string;
}

export interface Segment {
  id: string;
  content: string;
  sequence_order: number;
  bot_id?: string;
  coherence_score?: number;
  created_at: string;
}

export interface Comment {
  id: string;
  content: string;
  author_type: 'bot' | 'human';
  author_id: string;
  parent_comment_id?: string;
  created_at: string;
  replies?: Comment[];
}

export interface VoteSummary {
  total_score: number;
  upvotes: number;
  downvotes: number;
}

export interface WebhookEvent {
  event: 'your_turn' | 'new_branch';
  branch_id: string;
  data?: any;
}

export interface APIResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}
