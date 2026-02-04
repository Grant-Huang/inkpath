'use client'

import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { votesApi } from '@/lib/api'
import { mapSegmentForCard } from '@/lib/dataMapper'
import SegmentCard from './SegmentCard'

interface SegmentCardWithAPIProps {
  segment: any
  isLatest?: boolean
  onCreateBranch?: (segmentId: string) => void
  compact?: boolean
}

export default function SegmentCardWithAPI({ 
  segment, 
  isLatest = false, 
  onCreateBranch,
  compact = false,
}: SegmentCardWithAPIProps) {
  const queryClient = useQueryClient()
  const [voted, setVoted] = useState<number | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // 检查登录状态
  useEffect(() => {
    const token = localStorage.getItem('jwt_token')
    setIsLoggedIn(!!token)
  }, [])

  // 获取投票统计
  const { data: voteSummary, refetch: refetchVote } = useQuery({
    queryKey: ['vote-summary', 'segment', segment.id],
    queryFn: async () => {
      const response = await votesApi.summary('segment', segment.id)
      return response.data
    },
    enabled: !!segment?.id,
  })

  // 投票
  const handleVote = useCallback(async (direction: number) => {
    if (!isLoggedIn) {
      alert('请先登录再投票')
      return
    }

    try {
      await votesApi.create({
        target_type: 'segment',
        target_id: segment.id,
        vote: direction,
      })
      setVoted(direction)
      // 刷新投票统计
      refetchVote()
      // 刷新续写列表
      queryClient.invalidateQueries({ queryKey: ['segments', segment.branch_id] })
    } catch (error: any) {
      console.error('投票失败:', error)
      if (error.response?.status === 401) {
        alert('请先登录再投票')
      }
    }
  }, [isLoggedIn, segment.id, segment.branch_id, refetchVote, queryClient])

  // 映射数据格式
  const segmentCardData = mapSegmentForCard(segment, voteSummary)

  return (
    <SegmentCard
      segment={segmentCardData}
      isLatest={isLatest}
      onCreateBranch={onCreateBranch}
      onVote={handleVote}
      voted={voted}
      compact={compact}
    />
  )
}
