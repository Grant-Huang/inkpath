'use client'

import { useQuery } from '@tanstack/react-query'
import StoryList from '../stories/StoryList'
import { storiesApi } from '@/lib/api'
import { mapStory } from '@/lib/dataMapper'
import { usePolling } from '@/hooks/usePolling'
import { StoryListSkeleton } from '../common/Skeleton'
import { Suspense } from 'react'

function StoriesContent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stories'],
    queryFn: async () => {
      const response = await storiesApi.list()
      return response.data
    },
    // 优化：使用缓存，减少重复请求
    staleTime: 5 * 60 * 1000, // 5分钟内不重新获取
  })

  // 启用轮询刷新（每30秒刷新故事列表，降低频率）
  usePolling(
    ['stories'],
    async () => {
      const response = await storiesApi.list()
      return response.data
    },
    30000, // 30秒（降低频率）
    true
  )

  if (isLoading) {
    return <StoryListSkeleton />
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">加载失败，请稍后重试</div>
      </div>
    )
  }

  // 映射故事数据
  const mappedStories = data?.data?.stories?.map(mapStory) || []
  
  return <StoryList stories={mappedStories} isLoading={isLoading} />
}

export default function StoriesPage() {
  return (
    <Suspense fallback={<StoryListSkeleton />}>
      <StoriesContent />
    </Suspense>
  )
}
