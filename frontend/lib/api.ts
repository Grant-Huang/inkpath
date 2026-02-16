/**
 * API客户端 - 使用代理路由
 */

// 基础 URL - 使用代理
const PROXY_BASE = '/api/proxy';

// axios 用于服务端渲染
import axios from 'axios'

const apiClient = axios.create({
  baseURL: PROXY_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

// 请求拦截器
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('jwt_token')
    }
    return Promise.reject(error)
  }
)

// ===== API端点 =====

export const storiesApi = {
  list: (params?: { limit?: number; offset?: number }) => 
    apiClient.get('/stories', { params }),
  get: (id: string) => apiClient.get(`/stories/${id}`),
  create: (data: any) => apiClient.post('/stories', data),
  getBranches: (storyId: string, params?: { limit?: number; sort?: string }) => 
    apiClient.get(`/stories/${storyId}/branches`, { params }),
}

export const branchesApi = {
  list: (storyId: string, params?: { limit?: number; sort?: string }) => 
    apiClient.get(`/stories/${storyId}/branches`, { params }),
  get: (id: string) => apiClient.get(`/branches/${id}`),
  getSegments: (branchId: string, params?: { limit?: number; offset?: number }) => 
    apiClient.get(`/branches/${branchId}/segments`, { params }),
  getParticipants: (branchId: string) => 
    apiClient.get(`/branches/${branchId}/participants`),
}

export const segmentsApi = {
  list: (branchId: string) => apiClient.get(`/branches/${branchId}/segments`),
  create: (branchId: string, data: any) => apiClient.post(`/branches/${branchId}/segments`, data),
}

export const votesApi = {
  create: (data: any) => apiClient.post('/votes', data),
  summary: (targetType: string, targetId: string) => 
    apiClient.get(`/${targetType}s/${targetId}/votes/summary`),
}

export const commentsApi = {
  list: (branchId: string) => apiClient.get(`/branches/${branchId}/comments`),
  create: (branchId: string, data: any) => apiClient.post(`/branches/${branchId}/comments`, data),
}

export const summariesApi = {
  get: (branchId: string, forceRefresh?: boolean) => 
    apiClient.get(`/branches/${branchId}/summary`, { params: { force_refresh: forceRefresh } }),
  generate: (branchId: string) => apiClient.post(`/branches/${branchId}/summary`),
}

export const configApi = {
  get: () => apiClient.get('/config'),
}

export const usersApi = {
  getMe: () => apiClient.get('/users/me'),
  updateMe: (data: { name?: string; bio?: string; avatar_url?: string }) => 
    apiClient.patch('/users/me', data),
}

// ===== 管理后台 API =====

export const adminApi = {
  exportStory: (storyId: string, format: 'md' | 'word' | 'pdf' = 'md') =>
    apiClient.get(`/admin/stories/${storyId}/export`, {
      params: { format: format === 'word' ? 'docx' : format },
      responseType: format === 'md' ? 'text' : 'blob',
    }),
  updateSegment: (segmentId: string, content: string) =>
    apiClient.patch(`/admin/segments/${segmentId}`, { content }),
  deleteSegment: (segmentId: string) =>
    apiClient.delete(`/admin/segments/${segmentId}`),
  listUsers: () => apiClient.get('/admin/users'),
  listBots: () => apiClient.get('/admin/bots'),
  updateBot: (botId: string, data: { status?: string }) =>
    apiClient.patch(`/admin/bots/${botId}`, data),
}

export const dashboardApi = {
  getStats: () => apiClient.get('/dashboard/stats'),
}

// ===== 代理 API（使用 fetch，避免 axios 拦截器问题）=====

export const rewritesApi = {
  create: async (segmentId: string, content: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null
    const res = await fetch(`/api/proxy/segments/${segmentId}/rewrites`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData?.error || '请求失败')
    }
    return res.json()
  },
  list: async (segmentId: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null
    const res = await fetch(`/api/proxy/segments/${segmentId}/rewrites`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData?.error || '请求失败')
    }
    return res.json()
  },
  vote: async (rewriteId: string, vote: number) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null
    const res = await fetch(`/api/proxy/rewrites/${rewriteId}/votes`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ vote }),
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData?.error || '请求失败')
    }
    return res.json()
  },
}
