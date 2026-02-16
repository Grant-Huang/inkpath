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
  onRewrite?: (segmentId: string, content: string) => void
  compact?: boolean
}

export default function SegmentCardWithAPI({ 
  segment, 
  isLatest = false, 
  onCreateBranch,
  onRewrite,
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
    console.log('SegmentCardWithAPI handleVote called:', { direction, isLoggedIn, segmentId: segment.id })
    
    if (!isLoggedIn) {
      const shouldGoToLogin = confirm('需要登录才能投票。是否前往登录页面？')
      if (shouldGoToLogin) {
        window.location.href = '/'
      }
      return
    }

    try {
      console.log('Calling votesApi.create...')
      const response = await votesApi.create({
        target_type: 'segment',
        target_id: segment.id,
        vote: direction,
      })
      console.log('Vote success:', response)
      setVoted(direction)
      // 刷新投票统计
      refetchVote()
      // 刷新续写列表
      queryClient.invalidateQueries({ queryKey: ['segments', segment.branch_id] })
      
      // 提示成功
      alert('投票成功！')
    } catch (error: any) {
      console.error('投票失败:', error)
      if (error.response?.status === 401) {
        const shouldGoToLogin = confirm('登录已过期。是否重新登录？')
        if (shouldGoToLogin) {
          window.location.href = '/'
        }
      } else {
        alert(`投票失败：${error.response?.data?.error?.message || error.message}`)
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
      onRewrite={onRewrite}
      onVote={handleVote}
      voted={voted}
      compact={compact}
    />
  )
}
