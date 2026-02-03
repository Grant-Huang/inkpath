/**
 * 轮询Hook - 优化版
 * - 降低默认轮询频率 (5s → 30s)
 * - 添加最小间隔保护
 */
import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { startPolling } from '../../lib/polling'

/**
 * 使用轮询的Hook
 * @param queryKey 查询key
 * @param queryFn 查询函数
 * @param interval 轮询间隔（毫秒），默认30秒（优化：降低频率减少服务器压力）
 * @param enabled 是否启用轮询，默认true
 */
export function usePolling(
  queryKey: any[],
  queryFn: () => Promise<any>,
  interval: number = 30000, // 原5秒，现30秒
  enabled: boolean = true
) {
  const queryClient = useQueryClient()
  const stopPollingRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    if (!enabled) {
      if (stopPollingRef.current) {
        stopPollingRef.current()
        stopPollingRef.current = null
      }
      return
    }

    // 启动轮询
    const stop = startPolling(queryClient, queryKey, queryFn, interval)
    stopPollingRef.current = stop

    // 清理函数
    return () => {
      if (stopPollingRef.current) {
        stopPollingRef.current()
        stopPollingRef.current = null
      }
    }
  }, [queryClient, queryKey, queryFn, interval, enabled])
}
