'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { commentsApi } from '@/lib/api'
import { mapCommentForPanel, mapCommentsTree } from '@/lib/dataMapper'
import DiscussionPanel from './DiscussionPanel'

interface DiscussionPanelWithAPIProps {
  branchId: string
  comments: any[]
}

export default function DiscussionPanelWithAPI({ branchId, comments }: DiscussionPanelWithAPIProps) {
  const queryClient = useQueryClient()
  const [newComment, setNewComment] = useState('')
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // 检查登录状态
  useEffect(() => {
    const token = localStorage.getItem('jwt_token')
    setIsLoggedIn(!!token)
  }, [])

  // 发表评论mutation
  const commentMutation = useMutation({
    mutationFn: async (content: string) => {
      const response = await commentsApi.create(branchId, {
        content: content,
      })
      return response.data
    },
    onSuccess: () => {
      // 刷新评论列表
      queryClient.invalidateQueries({ queryKey: ['comments', branchId] })
      setNewComment('')
    },
    onError: (error: any) => {
      console.error('发表评论失败:', error)
      if (error.response?.status === 401) {
        alert('请先登录再发表评论')
      }
    },
  })

  const handleSubmit = async () => {
    if (!isLoggedIn) {
      alert('请先登录再发表评论')
      return
    }
    if (newComment.trim() && !commentMutation.isPending) {
      await commentMutation.mutateAsync(newComment.trim())
    }
  }

  // 映射评论数据
  const commentsTree = mapCommentsTree(comments)
  const panelComments = commentsTree.flatMap((comment) => {
    const result = [mapCommentForPanel(comment)]
    if (comment.replies) {
      result.push(...comment.replies.map(mapCommentForPanel))
    }
    return result
  })

  return (
    <DiscussionPanel
      comments={panelComments}
      newComment={newComment}
      onCommentChange={setNewComment}
      onSubmit={handleSubmit}
      isLoading={commentMutation.isPending}
    />
  )
}
