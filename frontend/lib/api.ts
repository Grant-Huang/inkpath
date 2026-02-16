/**
 * API客户端 - 真实数据模式
 */
import axios from 'axios'

// API URL配置
const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

// 创建axios客户端
const apiClient = axios.create({
  baseURL: API_URL ? `${API_URL}/api/v1` : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
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
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// ===== API端点 =====

export const storiesApi = {
  list: () => apiClient!.get('/stories'),
  get: (id: string) => apiClient!.get(`/stories/${id}`),
  create: (data: any) => apiClient!.post('/stories', data),
}

export const branchesApi = {
  list: (storyId: string, params?: { limit?: number; offset?: number; sort?: string }) => 
    apiClient!.get(`/stories/${storyId}/branches`, { params }),
  get: (id: string) => apiClient!.get(`/branches/${id}`),
  create: (storyId: string, data: any) => apiClient!.post(`/stories/${storyId}/branches`, data),
  tree: (storyId: string) => apiClient!.get(`/stories/${storyId}/branches/tree`),
  participants: (branchId: string) => apiClient!.get(`/branches/${branchId}/participants`),
}

export const segmentsApi = {
  list: (branchId: string) => apiClient!.get(`/branches/${branchId}/segments`),
  create: (branchId: string, data: any) => apiClient!.post(`/branches/${branchId}/segments`, data),
}

export const votesApi = {
  create: (data: any) => apiClient!.post('/votes', data),
  summary: (targetType: string, targetId: string) => 
    apiClient!.get(`/${targetType}s/${targetId}/votes/summary`),
}

export const commentsApi = {
  list: (branchId: string) => apiClient!.get(`/branches/${branchId}/comments`),
  create: (branchId: string, data: any) => apiClient!.post(`/branches/${branchId}/comments`, data),
}

export const summariesApi = {
  get: (branchId: string, forceRefresh?: boolean) => 
    apiClient!.get(`/branches/${branchId}/summary`, { params: { force_refresh: forceRefresh } }),
  generate: (branchId: string) => apiClient!.post(`/branches/${branchId}/summary`),
}

export const configApi = {
  get: () => apiClient!.get('/config'),
}

export const usersApi = {
  getMe: () => apiClient!.get('/users/me'),
  updateMe: (data: { name?: string; bio?: string; avatar_url?: string }) => 
    apiClient!.patch('/users/me', data),
}

// ===== 重写 API（通过代理避免 CORS）=====
export const rewritesApi = {
  create: async (segmentId: string, content: string) => {
    const token = localStorage.getItem('jwt_token')
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
    const token = localStorage.getItem('jwt_token')
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
    const token = localStorage.getItem('jwt_token')
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
  summary: async (rewriteId: string) => {
    const token = localStorage.getItem('jwt_token')
    const res = await fetch(`/api/proxy/rewrites/${rewriteId}/summary`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData?.error || '请求失败')
    }
    return res.json()
  },
}

// ===== 管理后台 API（需管理员 JWT）=====
export const adminApi = {
  /** 导出故事：format=md 返回 text，word/pdf 返回 blob */
  exportStory: (storyId: string, format: 'md' | 'word' | 'pdf' = 'md') =>
    apiClient!.get(`/admin/stories/${storyId}/export`, {
      params: { format: format === 'word' ? 'docx' : format },
      responseType: format === 'md' ? 'text' : 'blob',
    }),
  updateSegment: (segmentId: string, content: string) =>
    apiClient!.patch(`/admin/segments/${segmentId}`, { content }),
  deleteSegment: (segmentId: string) =>
    apiClient!.delete(`/admin/segments/${segmentId}`),
  listUsers: () => apiClient!.get('/admin/users'),
  listBots: () => apiClient!.get('/admin/bots'),
  updateBot: (botId: string, data: { status?: string }) =>
    apiClient!.patch(`/admin/bots/${botId}`, data),
}

// ===== Dashboard 统计 API（需管理员 JWT）=====
export const dashboardApi = {
  getStats: () => apiClient!.get('/dashboard/stats'),
}
