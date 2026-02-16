'use client'

import { useQuery, useQueries } from '@tanstack/react-query'
import { useState, useEffect, useRef } from 'react'
import ReadingView from '@/components/stories/ReadingView'
import { storiesApi, branchesApi, segmentsApi, commentsApi, summariesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { mapStory, mapBranch, mapCommentsTree } from '@/lib/dataMapper'
import SegmentCardWithAPI from '../segments/SegmentCardWithAPI'
import DiscussionPanelWithAPI from '../discussion/DiscussionPanelWithAPI'
import { usePolling } from '@/hooks/usePolling'
import { StoryDetailSkeleton } from '../common/Skeleton'
import { Suspense } from 'react'
import ErrorBoundary from '../common/ErrorBoundary'
import { useNewSegmentsMonitor, NewSegmentsButton, PullToAppend } from '../stories/NewSegmentsMonitor'

function StoryDetailContent({ storyId }: { storyId: string }) {
  const router = useRouter()
  const [selectedBranchId, setSelectedBranchId] = useState<string | null>(null)
  const [displayedSegments, setDisplayedSegments] = useState<any[]>([])
  const [hasNewContent, setHasNewContent] = useState(false)
  const segmentsQueryRef = useRef<any>(null)

  // 优化：并行请求 + 重试机制
  const [storyQuery, branchesQuery] = useQueries({
    queries: [
      {
        queryKey: ['story', storyId],
        queryFn: async () => {
          const response = await storiesApi.get(storyId)
          return response.data
        },
        staleTime: 5 * 60 * 1000,
        retry: 2,
      },
      {
        queryKey: ['branches', storyId],
        queryFn: async () => {
          const response = await storiesApi.getBranches(storyId, { limit: 6 })
          return response.data
        },
        staleTime: 2 * 60 * 1000,
        retry: 2,
      },
    ],
  })

  const { data: story, isLoading: storyLoading } = storyQuery
  const { data: branches, isLoading: branchesLoading } = branchesQuery

  // 分支列表
  const branchesList = branches?.data?.branches || []
  useEffect(() => {
    if (!selectedBranchId && branchesList.length > 0) {
      const mainBranch = branchesList.find((b: any) => !b.parent_branch_id)
      const defaultBranchId = mainBranch?.id || branchesList[0]?.id
      if (defaultBranchId) {
        setSelectedBranchId(defaultBranchId)
      }
    }
  }, [branchesList, selectedBranchId])

  // 片段查询
  const segmentsQuery = useQuery({
    queryKey: ['segments', selectedBranchId],
    queryFn: async () => {
      if (!selectedBranchId) return { data: { segments: [] } }
      const response = await segmentsApi.list(selectedBranchId)
      return response.data
    },
    enabled: !!selectedBranchId,
  })

  segmentsQueryRef.current = segmentsQuery

  // 评论查询
  const commentsQuery = useQuery({
    queryKey: ['comments', selectedBranchId],
    queryFn: async () => {
      if (!selectedBranchId) return { data: { comments: [] } }
      const response = await commentsApi.list(selectedBranchId)
      return response.data
    },
    enabled: !!selectedBranchId,
  })

  // 摘要查询
  const { data: summary } = useQuery({
    queryKey: ['summary', selectedBranchId],
    queryFn: async () => {
      if (!selectedBranchId) return null
      const response = await summariesApi.get(selectedBranchId)
      return response.data
    },
    enabled: !!selectedBranchId,
    staleTime: 5 * 60 * 1000,
  })

  // 初始化显示片段
  useEffect(() => {
    const segments = segmentsQuery.data?.data?.segments || []
    if (segments.length > 0 && displayedSegments.length === 0) {
      setDisplayedSegments(segments)
    }
  }, [segmentsQuery.data, displayedSegments.length])

  // 新片段监测
  const { newSegmentsCount, pendingSegments, startMonitoring, loadNewSegments } = useNewSegmentsMonitor({
    branchId: selectedBranchId,
    initialSegments: displayedSegments,
    enabled: !!selectedBranchId,
    onNewSegments: (newOnes) => {
      setDisplayedSegments(prev => [...prev, ...newOnes])
      setHasNewContent(true)
    }
  })

  // 用户点击查看新片段
  const handleShowNewSegments = async () => {
    await loadNewSegments()
  }

  // 移动端上拉加载
  const handlePullToAppend = async () => {
    if (newSegmentsCount > 0 && pendingSegments.length > 0) {
      await handleShowNewSegments()
    } else if (segmentsQueryRef.current) {
      // 刷新获取最新片段
      await segmentsQueryRef.current.refetch()
      const segments = segmentsQueryRef.current.data?.data?.segments || []
      setDisplayedSegments(segments)
    }
  }

  // 开始监测（页面可见时）
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        startMonitoring()
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    startMonitoring()
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [startMonitoring])

  // 轮询（桌面端30秒，移动端60秒）
  usePolling(
    ['segments', selectedBranchId],
    async () => {
      if (!selectedBranchId) return { data: { segments: [] } }
      const response = await segmentsApi.list(selectedBranchId)
      return response.data
    },
    30000,
    !!selectedBranchId
  )

  usePolling(
    ['comments', selectedBranchId],
    async () => {
      if (!selectedBranchId) return { data: { comments: [] } }
      const response = await commentsApi.list(selectedBranchId)
      return response.data
    },
    30000,
    !!selectedBranchId
  )

  if (storyLoading || branchesLoading) {
    return <StoryDetailSkeleton />
  }

  // 映射数据（segments 传原始 API 数据，由 SegmentCardWithAPI 内部做 mapSegmentForCard，避免重复映射导致 bot/time 丢失）
  const mappedStory = story?.data ? mapStory(story.data) : null
  const mappedBranches = branches?.data?.branches?.map(mapBranch) || []
  const segmentsForView =
    displayedSegments.length > 0
      ? displayedSegments
      : (segmentsQuery.data?.data?.segments || [])
  const mappedComments = commentsQuery.data?.data?.comments || []

  if (!mappedStory) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-[#7a6f65]">故事不存在或已被删除</div>
      </div>
    )
  }

  return (
    <>
      <ReadingView
        story={mappedStory}
        branches={mappedBranches}
        segments={segmentsForView}
        comments={mappedComments}
        summary={summary?.data}
        selectedBranchId={selectedBranchId}
        onBranchSelect={setSelectedBranchId}
        storyId={storyId}
        onBack={() => router.push('/')}
        onPullToAppend={handlePullToAppend}
        hasNewContent={hasNewContent}
        newSegmentsCount={newSegmentsCount}
      />
      
      {/* 新片段悬浮按钮 */}
      <NewSegmentsButton
        count={newSegmentsCount}
        onClick={handleShowNewSegments}
        onClose={() => setDisplayedSegments(prev => {
          // 保留已显示的片段，忽略新片段
          const lastKnownId = displayedSegments[displayedSegments.length - 1]?.id
          return prev
        })}
      />
    </>
  )
}

export default function StoryDetailPage({ storyId }: { storyId: string }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<StoryDetailSkeleton />}>
        <StoryDetailContent storyId={storyId} />
      </Suspense>
    </ErrorBoundary>
  )
}
