'use client'

import { useQuery, useQueries } from '@tanstack/react-query'
import ReadingView from '../stories/ReadingView'
import { storiesApi, branchesApi, segmentsApi, commentsApi, summariesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { mapStory, mapBranch, mapSegmentForCard, mapCommentsTree } from '@/lib/dataMapper'
import SegmentCardWithAPI from '../segments/SegmentCardWithAPI'
import DiscussionPanelWithAPI from '../discussion/DiscussionPanelWithAPI'
import { usePolling } from '@/hooks/usePolling'
import { StoryDetailSkeleton } from '../common/Skeleton'
import { Suspense } from 'react'

function StoryDetailContent({ storyId }: { storyId: string }) {
  const router = useRouter()

  // 优化：并行请求 story 和 branches，而不是串行
  const [storyQuery, branchesQuery] = useQueries({
    queries: [
      {
        queryKey: ['story', storyId],
        queryFn: async () => {
          const response = await storiesApi.get(storyId)
          return response.data
        },
        staleTime: 5 * 60 * 1000, // 5分钟内不重新获取
      },
      {
        queryKey: ['branches', storyId],
        queryFn: async () => {
          const response = await branchesApi.list(storyId, { limit: 6, sort: 'activity' })
          return response.data
        },
        staleTime: 2 * 60 * 1000, // 2分钟内不重新获取
      },
    ],
  })

  const { data: story, isLoading: storyLoading } = storyQuery
  const { data: branches, isLoading: branchesLoading } = branchesQuery

  // 获取选中分支的续写段
  const selectedBranchId = branches?.data?.branches?.[0]?.id
  
  const segmentsQuery = useQuery({
    queryKey: ['segments', selectedBranchId],
    queryFn: async () => {
      if (!selectedBranchId) return { data: { segments: [] } }
      const response = await segmentsApi.list(selectedBranchId)
      return response.data
    },
    enabled: !!selectedBranchId,
  })

  const commentsQuery = useQuery({
    queryKey: ['comments', selectedBranchId],
    queryFn: async () => {
      if (!selectedBranchId) return { data: { comments: [] } }
      const response = await commentsApi.list(selectedBranchId)
      return response.data
    },
    enabled: !!selectedBranchId,
  })

  const { data: segments } = segmentsQuery
  const { data: comments } = commentsQuery

  // 获取摘要（延迟加载，不阻塞主内容）
  const { data: summary } = useQuery({
    queryKey: ['summary', selectedBranchId],
    queryFn: async () => {
      if (!selectedBranchId) return null
      const response = await summariesApi.get(selectedBranchId)
      return response.data
    },
    enabled: !!selectedBranchId,
    staleTime: 5 * 60 * 1000, // 摘要5分钟内不重新获取
  })

  // 优化：降低轮询频率，减少服务器压力
  usePolling(
    ['segments', selectedBranchId],
    async () => {
      if (!selectedBranchId) return { data: { segments: [] } }
      const response = await segmentsApi.list(selectedBranchId)
      return response.data
    },
    15000, // 15秒（降低频率）
    !!selectedBranchId
  )

  usePolling(
    ['comments', selectedBranchId],
    async () => {
      if (!selectedBranchId) return { data: { comments: [] } }
      const response = await commentsApi.list(selectedBranchId)
      return response.data
    },
    15000, // 15秒（降低频率）
    !!selectedBranchId
  )

  if (storyLoading || branchesLoading) {
    return <StoryDetailSkeleton />
  }

  // 映射数据
  const mappedStory = story?.data ? mapStory(story.data) : null
  const mappedBranches = branches?.data?.branches?.map(mapBranch) || []
  const mappedSegments = segments?.data?.segments || []
  const mappedComments = comments?.data?.comments || []

  if (!mappedStory) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">故事不存在</div>
      </div>
    )
  }

  return (
    <ReadingView
      story={mappedStory}
      branches={mappedBranches}
      segments={mappedSegments}
      comments={mappedComments}
      summary={summary?.data}
      selectedBranchId={selectedBranchId}
      storyId={storyId}
      onBack={() => router.push('/')}
    />
  )
}

export default function StoryDetailPage({ storyId }: { storyId: string }) {
  return (
    <Suspense fallback={<StoryDetailSkeleton />}>
      <StoryDetailContent storyId={storyId} />
    </Suspense>
  )
}
