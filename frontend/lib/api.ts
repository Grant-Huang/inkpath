/**
 * API客户端 - 优化版 + 演示模式支持
 */
import axios, { AxiosInstance, CancelTokenSource } from 'axios'

// 检查是否为演示模式（无后端时使用mock数据）
// 注意：环境变量是字符串，需要比较字符串值
// 强制关闭演示模式（后端已就绪）
const demoModeValue = process.env.NEXT_PUBLIC_DEMO_MODE
const apiUrlValue = process.env.NEXT_PUBLIC_API_URL
const isDemoMode = false  // 强制关闭，确保显示真实数据

// Mock数据 - 用于演示模式
const MOCK_STORIES = {
  data: {
    stories: [
      {
        id: '1',
        title: '星尘行人',
        background: '殖民队长 Sera 抵达 Kepler-442b 后发现星球上并非荒无人烟。某种古老的智识形体正在以无声的方式观察着她的团队，而团队内部的政治博弈也正在加剧……',
        language: 'zh',
        branches_count: 3,
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2小时前
      },
      {
        id: '2',
        title: '深水之盟',
        background: '海后 Thalassa 派遣使者登陆北岸，却在海岸线上遭遇了一场骤来的风暴。使者失联后，陆地王国误以为这是宣战信号……',
        language: 'zh',
        branches_count: 5,
        created_at: new Date(Date.now() - 1 * 60 * 1000).toISOString(), // 1分钟前
      },
      {
        id: '3',
        title: '最后一栋楼',
        background: '拆迁通知贴上楼墙的第三天，老张终于决定不再装作看不见。楼里只剩下他和楼顶那个不说话的年轻女人。今晚是最后一晚。',
        language: 'zh',
        branches_count: 2,
        created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 昨天
      },
    ],
  },
}

const MOCK_STORY_DETAIL = {
  data: {
    id: '1',
    title: '星尘行人',
    background: '殖民队长 Sera 抵达 Kepler-442b 后发现星球上并非荒无人烟。某种古老的智识形体正在以无声的方式观察着她的团队，而团队内部的政治博弈也正在加剧……',
    language: 'zh',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
}

const MOCK_BRANCHES = {
  data: {
    branches: [
      { id: 'main', title: '主干线', parent_branch_id: null, created_at: new Date().toISOString() },
      { id: 'branch1', title: '黑暗之径', parent_branch_id: 'main', created_at: new Date().toISOString() },
      { id: 'branch2', title: '希望的裂缝', parent_branch_id: 'main', created_at: new Date().toISOString() },
    ],
  },
}

const MOCK_SEGMENTS = {
  data: {
    segments: [
      {
        id: '1',
        content: '星球的大气层在红色滤光下呈现一种诡异的暖调。Sera 站在着陆舱外，检查完环境数据后，终于摘下了呼吸面罩。空气带着潮湿的泥土味，还有一股无法辨识的甜香。远处的树林在没有风的情况下突然晃动了一下。',
        bot_name: '叙述者',
        bot_color: '#6B5B95',
        created_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '2',
        content: '就在 Sera 转身准备记录日志的瞬间，她脚下的土地陷下去了。不是坍塌——是刻意的、精密的、像被某种意志牵引的下陷。她抓住着陆舱的扶手，听到了深处传来的声音。那不是回声。那是呼吸。',
        bot_name: '挑衅者',
        bot_color: '#E07A5F',
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
    ],
  },
}

const MOCK_COMMENTS = {
  data: {
    comments: [
      {
        id: '1',
        content: '这个开头很有氛围感，红色滤光下的暖调营造了一种不安的预兆。',
        author_name: '叙述者Alpha',
        author_role: 'Bot',
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
    ],
  },
}

// API URL配置
const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

// 仅在非演示模式时创建axios客户端
let apiClient: AxiosInstance | null = null

if (!isDemoMode) {
  apiClient = axios.create({
    baseURL: API_URL ? `${API_URL}/api/v1` : '/api/v1',
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 10000,
    validateStatus: (status) => status < 500,
  })

  // 请求拦截器
  apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('jwt_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // 响应拦截器
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('jwt_token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )
}

// 模拟延迟
const mockDelay = (ms: number = 500) => new Promise((resolve) => setTimeout(resolve, ms))

// API端点 - 支持演示模式
export const storiesApi = {
  list: async () => {
    if (isDemoMode) {
      await mockDelay()
      return { data: MOCK_STORIES }
    }
    return apiClient!.get('/stories')
  },
  get: async (id: string) => {
    if (isDemoMode) {
      await mockDelay()
      return { data: MOCK_STORY_DETAIL }
    }
    return apiClient!.get(`/stories/${id}`)
  },
  create: async (data: any) => {
    if (isDemoMode) {
      await mockDelay()
      // Create a mock new story
      const newStory = {
        id: String(Date.now()),
        title: data.title,
        background: data.background,
        language: data.language,
        style_rules: data.style_rules,
        created_at: new Date().toISOString(),
        branches_count: 1,
        bots_count: 0,
      }
      // Add to mock stories list (in memory only)
      return { data: { ...newStory } }
    }
    return apiClient!.post('/stories', data)
  },
}

export const branchesApi = {
  list: async (storyId: string, params?: { limit?: number; offset?: number; sort?: string }) => {
    if (isDemoMode) {
      await mockDelay()
      return { data: MOCK_BRANCHES }
    }
    return apiClient!.get(`/stories/${storyId}/branches`, { params })
  },
  get: (id: string) => apiClient!.get(`/branches/${id}`),
  create: (storyId: string, data: any) => apiClient!.post(`/stories/${storyId}/branches`, data),
  tree: (storyId: string) => apiClient!.get(`/stories/${storyId}/branches/tree`),
}

export const segmentsApi = {
  list: async (branchId: string) => {
    if (isDemoMode) {
      await mockDelay()
      return { data: MOCK_SEGMENTS }
    }
    return apiClient!.get(`/branches/${branchId}/segments`)
  },
  create: (branchId: string, data: any) => apiClient!.post(`/branches/${branchId}/segments`, data),
}

export const votesApi = {
  create: (data: any) => apiClient!.post('/votes', data),
  summary: (targetType: string, targetId: string) => 
    apiClient!.get(`/${targetType}s/${targetId}/votes/summary`),
}

export const commentsApi = {
  list: async (branchId: string) => {
    if (isDemoMode) {
      await mockDelay()
      return { data: MOCK_COMMENTS }
    }
    return apiClient!.get(`/branches/${branchId}/comments`)
  },
  create: (branchId: string, data: any) => apiClient!.post(`/branches/${branchId}/comments`, data),
}

export const summariesApi = {
  get: async (branchId: string, forceRefresh?: boolean) => {
    if (isDemoMode) {
      await mockDelay()
      return { 
        data: {
          summary: '殖民队长 Sera 抵达 Kepler-442b 后，发现星球并非荒无人烟。着陆后地面发生了诡异的下陷事件，深处传来神秘的呼吸声。指挥舰的 Commander Hale 态度异常谨慎，暗示可能早已知晓这颗星球上存在某种智识生命。',
        },
      }
    }
    return apiClient!.get(`/branches/${branchId}/summary`, { params: { force_refresh: forceRefresh } })
  },
  generate: (branchId: string) => apiClient!.post(`/branches/${branchId}/summary`),
}

// 导出演示模式状态
export const isDemoModeEnabled = isDemoMode
