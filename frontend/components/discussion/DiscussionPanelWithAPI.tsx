'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { commentsApi } from '../lib/api'
import { mapCommentForPanel, mapCommentsTree } from '../lib/dataMapper'
import DiscussionPanel from './DiscussionPanel'

interface DiscussionPanelWithAPIProps {
  branchId: string
  comments: any[]
}

export default function DiscussionPanelWithAPI({ branchId, comments }: DiscussionPanelWithAPIProps) {
  const queryClient = useQueryClient()
  const [newComment, setNewComment] = useState('')

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
  })

  const handleSubmit = async () => {
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
