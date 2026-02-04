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
      window.location.href = '/login'
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

// ===== 重写 API =====
export const rewritesApi = {
  create: (segmentId: string, content: string) => 
    apiClient!.post(`/segments/${segmentId}/rewrites`, { content }),
  list: (segmentId: string) => 
    apiClient!.get(`/segments/${segmentId}/rewrites`),
  vote: (rewriteId: string, vote: number) => 
    apiClient!.post(`/rewrites/${rewriteId}/votes`, { vote }),
  summary: (rewriteId: string) => 
    apiClient!.get(`/rewrites/${rewriteId}/summary`),
}
