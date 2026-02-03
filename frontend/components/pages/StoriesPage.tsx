'use client'

import { useQuery } from '@tanstack/react-query'
import StoryList from '@/components/stories/StoryList'
import { storiesApi } from '@/lib/api'
import { mapStory } from '@/lib/dataMapper'
import { usePolling } from '@/hooks/usePolling'
import { StoryListSkeleton } from '../common/Skeleton'
import { Suspense } from 'react'
import ErrorBoundary from '../common/ErrorBoundary'

function StoriesContent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stories'],
    queryFn: async () => {
      const response = await storiesApi.list()
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5分钟内不重新获取
    retry: 2, // 优化：添加重试机制
  })

  // 启用轮询刷新（每30秒刷新故事列表，降低频率）
  usePolling(
    ['stories'],
    async () => {
      const response = await storiesApi.list()
      return response.data
    },
    30000,
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

  const mappedStories = data?.data?.stories?.map(mapStory) || []
  return <StoryList stories={mappedStories} isLoading={isLoading} />
}

export default function StoriesPage() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<StoryListSkeleton />}>
        <StoriesContent />
      </Suspense>
    </ErrorBoundary>
  )
}
