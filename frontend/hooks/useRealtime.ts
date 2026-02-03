/**
 * 实时刷新Hook - 统一管理实时刷新逻辑
 */
import { useEffect, useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { startPolling } from '../../lib/polling'

interface RealtimeConfig {
  enabled?: boolean
  interval?: number
  onError?: (error: Error) => void
}

/**
 * 使用实时刷新的Hook
 * 支持多个查询的实时刷新
 */
export function useRealtime(
  queries: Array<{
    queryKey: any[]
    queryFn: () => Promise<any>
    interval?: number
  }>,
  config: RealtimeConfig = {}
) {
  const queryClient = useQueryClient()
  const { enabled = true, onError } = config
  const [isConnected, setIsConnected] = useState(true)
  const stopFunctionsRef = useRef<(() => void)[]>([])

  useEffect(() => {
    if (!enabled) {
      // 停止所有轮询
      stopFunctionsRef.current.forEach(stop => stop())
      stopFunctionsRef.current = []
      return
    }

    // 启动所有查询的轮询
    const stops = queries.map(({ queryKey, queryFn, interval = 5000 }) => {
      return startPolling(
        queryClient,
        queryKey,
        async () => {
          try {
            await queryFn()
            setIsConnected(true)
          } catch (error) {
            setIsConnected(false)
            if (onError && error instanceof Error) {
              onError(error)
            }
          }
        },
        interval
      )
    })

    stopFunctionsRef.current = stops

    // 清理函数
    return () => {
      stops.forEach(stop => stop())
    }
  }, [queryClient, enabled, onError, JSON.stringify(queries)])

  return { isConnected }
}
