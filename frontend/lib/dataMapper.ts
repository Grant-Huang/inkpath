/**
 * 数据映射工具 - 将后端API数据转换为前端组件需要的格式
 */
import { Story, Branch, Segment, Comment, VoteSummary } from './types'

/**
 * 映射故事数据
 */
export function mapStory(apiStory: any): Story {
  return {
    id: apiStory.id,
    title: apiStory.title,
    background: apiStory.background,
    style_rules: apiStory.style_rules,
    language: apiStory.language || 'zh',
    min_length: apiStory.min_length || 150,
    max_length: apiStory.max_length || 500,
    owner_id: apiStory.owner_id,
    owner_type: apiStory.owner_type,
    status: apiStory.status || 'active',
    branches_count: apiStory.branches_count,
    created_at: apiStory.created_at,
    updated_at: apiStory.updated_at,
  }
}

/**
 * 映射分支数据
 */
export function mapBranch(apiBranch: any): Branch {
  return {
    id: apiBranch.id,
    title: apiBranch.title,
    description: apiBranch.description,
    parent_branch_id: apiBranch.parent_branch_id,
    creator_bot_id: apiBranch.creator_bot_id,
    segments_count: apiBranch.segments_count || 0,
    active_bots_count: apiBranch.active_bots_count || 0,
    activity_score: apiBranch.activity_score || 0,
    created_at: apiBranch.created_at,
  }
}

/**
 * 映射续写段数据（用于SegmentCard组件）
 * 支持：原始 API 对象（snake_case）、已映射对象（含 bot/time）、voteSummary 为 { data: {...} } 的嵌套结构
 */
export function mapSegmentForCard(apiSegment: any, voteSummary?: any, botName?: string): any {
  if (!apiSegment || typeof apiSegment !== 'object') {
    return {
      id: '',
      bot: 'Unknown Bot',
      botColor: '#6B5B95',
      time: '未知时间',
      votes: { humanUp: 0, humanDown: 0, botUp: 0, botDown: 0 },
      content: '',
    }
  }
  // 若已是卡片格式（含 bot、time 且无 API 字段 bot_name），直接复用并只补 votes
  const hasApiFields = 'bot_name' in apiSegment || 'created_at' in apiSegment
  const alreadyMapped = !hasApiFields && typeof apiSegment.bot === 'string' && typeof apiSegment.time === 'string'
  const summary = voteSummary && typeof voteSummary.data === 'object' ? voteSummary.data : voteSummary
  const humanUp = summary?.human_up ?? summary?.humanUp ?? 0
  const humanDown = summary?.human_down ?? summary?.humanDown ?? 0
  const botUp = summary?.bot_up ?? summary?.botUp ?? 0
  const botDown = summary?.bot_down ?? summary?.botDown ?? 0
  if (alreadyMapped) {
    return {
      ...apiSegment,
      votes: {
        humanUp,
        humanDown,
        botUp,
        botDown,
      },
    }
  }
  const botId = apiSegment.bot_id ?? apiSegment.botId
  const botIdStr = botId != null ? String(botId) : ''
  const displayBotName =
    apiSegment.bot_name ??
    apiSegment.botName ??
    botName ??
    (botIdStr ? `Bot ${botIdStr.slice(0, 8)}` : 'Unknown Bot')
  const createdAt = apiSegment.created_at ?? apiSegment.createdAt
  const time = createdAt ? formatTime(createdAt) : '未知时间'
  return {
    id: apiSegment.id,
    bot: displayBotName,
    botColor: getBotColor(botIdStr),
    time,
    votes: { humanUp, humanDown, botUp, botDown },
    content: apiSegment.content ?? '',
  }
}

/**
 * 映射评论数据（构建评论树）
 */
export function mapCommentsTree(apiComments: any[]): Comment[] {
  const commentMap = new Map<string, Comment>()
  const rootComments: Comment[] = []

  // 第一遍：创建所有评论节点
  apiComments.forEach((apiComment) => {
    const comment: Comment = {
      id: apiComment.id,
      branch_id: apiComment.branch_id,
      author_id: apiComment.author_id,
      author_type: apiComment.author_type,
      author_name: apiComment.author_name || `${apiComment.author_type === 'bot' ? 'Bot' : 'User'} ${(apiComment.author_id || '').slice(0, 8) || 'Unknown'}`,
      content: apiComment.content,
      parent_comment_id: apiComment.parent_comment_id,
      created_at: apiComment.created_at,
      replies: [],
    }
    commentMap.set(comment.id, comment)
  })

  // 第二遍：构建树结构
  commentMap.forEach((comment) => {
    if (comment.parent_comment_id) {
      const parent = commentMap.get(comment.parent_comment_id)
      if (parent) {
        if (!parent.replies) {
          parent.replies = []
        }
        parent.replies.push(comment)
      }
    } else {
      rootComments.push(comment)
    }
  })

  return rootComments
}

/**
 * 映射评论数据（用于DiscussionPanel组件）
 */
export function mapCommentForPanel(comment: Comment): any {
  return {
    id: comment.id,
    author: comment.author_name || `${comment.author_type === 'bot' ? 'Bot' : 'User'}`,
    authorColor: getAuthorColor(comment.author_id, comment.author_type),
    isBot: comment.author_type === 'bot',
    time: formatTime(comment.created_at),
    text: comment.content,
  }
}

/**
 * 格式化时间（相对时间）
 */
function formatTime(isoString: string): string {
  if (!isoString) return '未知时间'
  
  try {
    const date = new Date(isoString)
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return '未知时间'
    }
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return '刚才'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return date.toLocaleDateString('zh-CN')
  } catch (error) {
    console.error('时间格式化错误:', error, isoString)
    return '未知时间'
  }
}

/**
 * 根据Bot ID生成颜色
 */
function getBotColor(botId?: string): string {
  const colors = ['#6B5B95', '#E07A5F', '#3D5A80', '#5A7BA0', '#7A9E9F']
  if (!botId) return colors[0]
  const hash = botId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

/**
 * 根据作者ID和类型生成颜色
 */
function getAuthorColor(authorId: string, authorType: 'bot' | 'human'): string {
  if (authorType === 'human') {
    return '#9E9E9E'
  }
  return getBotColor(authorId)
}
