'use client'

import { useState } from 'react'
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

  // 获取投票统计
  const { data: voteSummary } = useQuery({
    queryKey: ['vote-summary', 'segment', segment.id],
    queryFn: async () => {
      const response = await votesApi.summary('segment', segment.id)
      return response.data
    },
  })

  // 投票mutation
  const voteMutation = useMutation({
    mutationFn: async (vote: number) => {
      const response = await votesApi.create({
        target_type: 'segment',
        target_id: segment.id,
        vote: vote,
      })
      return response.data
    },
    onSuccess: () => {
      // 刷新投票统计
      queryClient.invalidateQueries({ queryKey: ['vote-summary', 'segment', segment.id] })
      // 刷新续写段列表
      queryClient.invalidateQueries({ queryKey: ['segments', segment.branch_id] })
    },
  })

  const handleVote = async (direction: number) => {
    // 检查是否已经投票
    if (voted !== null) {
      // 如果点击的是已投票的方向，取消投票
      if (voted === direction) {
        // 取消投票（发送相反方向的投票）
        await voteMutation.mutateAsync(-direction)
        setVoted(null)
      } else {
        // 改变投票方向
        await voteMutation.mutateAsync(direction)
        setVoted(direction)
      }
    } else {
      // 新投票
      await voteMutation.mutateAsync(direction)
      setVoted(direction)
    }
  }

  // 映射数据格式
  const segmentCardData = mapSegmentForCard(segment, voteSummary?.data)

  return (
    <SegmentCard
      segment={segmentCardData}
      isLatest={isLatest}
      onCreateBranch={onCreateBranch}
      onVote={handleVote}
      voted={voted}
      isLoading={voteMutation.isPending}
      compact={compact}
    />
  )
}
