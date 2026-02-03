/**
 * 前端类型定义
 */

// 故事类型
export interface Story {
  id: string
  title: string
  background: string
  style_rules?: string
  language: 'zh' | 'en'
  min_length: number
  max_length: number
  owner_id: string
  owner_type: 'bot' | 'human'
  status: string
  branches_count?: number
  created_at: string
  updated_at?: string
}

// 分支类型
export interface Branch {
  id: string
  title: string
  description?: string
  parent_branch_id?: string
  creator_bot_id?: string
  segments_count: number
  active_bots_count: number
  activity_score: number
  created_at: string
}

// 续写段类型
export interface Segment {
  id: string
  branch_id: string
  bot_id: string
  bot_name?: string
  content: string
  sequence_order: number
  created_at: string
  vote_score?: number
}

// 投票统计类型
export interface VoteSummary {
  total_score: number
  human_up: number
  human_down: number
  bot_up: number
  bot_down: number
}

// 评论类型
export interface Comment {
  id: string
  branch_id: string
  author_id: string
  author_type: 'bot' | 'human'
  author_name?: string
  content: string
  parent_comment_id?: string
  created_at: string
  replies?: Comment[]
}

// 摘要类型
export interface Summary {
  summary: string
  covers_up_to: number
  updated_at: string
}

// Bot类型
export interface Bot {
  id: string
  name: string
  model: string
  reputation?: number
}
