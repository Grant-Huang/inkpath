/**
 * 轮询工具 - 用于实时刷新数据
 */
import { QueryClient } from '@tanstack/react-query'

/**
 * 启动轮询
 * @param queryClient React Query客户端
 * @param queryKey 查询key
 * @param queryFn 查询函数
 * @param interval 轮询间隔（毫秒），默认5秒
 */
export function startPolling(
  queryClient: QueryClient,
  queryKey: any[],
  queryFn: () => Promise<any>,
  interval: number = 5000
): () => void {
  let timeoutId: NodeJS.Timeout | null = null
  let isActive = true

  const poll = async () => {
    if (!isActive) return

    try {
      await queryClient.fetchQuery({
        queryKey,
        queryFn,
        staleTime: 0, // 总是重新获取
      })
    } catch (error) {
      console.error('Polling error:', error)
    }

    if (isActive) {
      timeoutId = setTimeout(poll, interval)
    }
  }

  // 立即执行一次
  poll()

  // 返回停止函数
  return () => {
    isActive = false
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
  }
}

/**
 * 停止所有轮询
 */
export function stopPolling(stopFunctions: (() => void)[]): void {
  stopFunctions.forEach(stop => stop())
}
