/**
 * 预加载Hook
 * 用户悬停时预加载数据，提升感知速度
 */
'use client'

import { useQueryClient } from '@tanstack/react-query'
import { storiesApi, branchesApi } from '@/lib/api'
import { useCallback } from 'react'

/**
 * 预加载故事数据
 * 当用户悬停在故事卡片上时调用
 */
export function useStoryPrefetch() {
  const queryClient = useQueryClient()

  const prefetchStory = useCallback(async (storyId: string) => {
    await queryClient.prefetchQuery({
      queryKey: ['story', storyId],
      queryFn: async () => {
        const response = await storiesApi.get(storyId)
        return response.data
      },
      staleTime: 5 * 60 * 1000,
    })

    // 同时预加载分支
    await queryClient.prefetchQuery({
      queryKey: ['branches', storyId],
      queryFn: async () => {
        const response = await branchesApi.list(storyId, { limit: 6, sort: 'activity' })
        return response.data
      },
      staleTime: 2 * 60 * 1000,
    })
  }, [queryClient])

  return { prefetchStory }
}

export default useStoryPrefetch
