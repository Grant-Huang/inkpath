'use client'

import { QueryClient, QueryClientProvider as TanStackQueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryClientProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // 性能优化配置
        refetchOnWindowFocus: false, // 窗口聚焦时不重新获取
        refetchOnMount: false, // 组件挂载时不重新获取（如果数据未过期）
        refetchOnReconnect: true, // 网络重连时重新获取
        retry: 1, // 失败时重试1次
        retryDelay: 1000, // 重试延迟1秒
        staleTime: 5 * 60 * 1000, // 数据5分钟内视为新鲜，不重新获取
        gcTime: 10 * 60 * 1000, // 缓存10分钟后清理（原 cacheTime）
        // 并行请求优化
        networkMode: 'online', // 只在在线时请求
      },
      mutations: {
        retry: 1,
        retryDelay: 1000,
      },
    },
  }))

  return (
    <TanStackQueryClientProvider client={queryClient}>
      {children}
    </TanStackQueryClientProvider>
  )
}
