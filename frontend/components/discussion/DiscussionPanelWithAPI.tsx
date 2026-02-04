'use client'

import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { commentsApi, rewritesApi } from '@/lib/api'
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
  const [showRewrites, setShowRewrites] = useState(false)
  const [topRewrite, setTopRewrite] = useState<any>(null)
  const [isLoadingRewrite, setIsLoadingRewrite] = useState(false)

  // 检查登录状态
  useEffect(() => {
    const token = localStorage.getItem('jwt_token')
    setIsLoggedIn(!!token)
  }, [])

  // 获取最高评分重写
  useEffect(() => {
    if (showRewrites) {
      loadTopRewrite()
    }
  }, [showRewrites])

  const loadTopRewrite = async () => {
    setIsLoadingRewrite(true)
    try {
      // 获取所有重写，然后找评分最高的
      const res = await rewritesApi.list(comments[0]?.id || '')
      if (res.data?.data?.rewrites?.length > 0) {
        const rewrites = res.data.data.rewrites
        // 按评分排序
        rewrites.sort((a: any, b: any) => 
          (b.vote_summary?.total_score || 0) - (a.vote_summary?.total_score || 0)
        )
        setTopRewrite(rewrites[0])
      } else {
        setTopRewrite(null)
      }
    } catch (e) {
      console.error('加载重写失败:', e)
      setTopRewrite(null)
    } finally {
      setIsLoadingRewrite(false)
    }
  }

  // 发表评论mutation
  const commentMutation = {
    mutateAsync: async (content: string) => {
      const response = await commentsApi.create(branchId, {
        content: content,
      })
      return response.data
    },
    isPending: false,
  }

  const handleSubmit = async () => {
    if (!isLoggedIn) {
      alert('请先登录再发表评论')
      return
    }
    if (newComment.trim() && !commentMutation.isPending) {
      await commentMutation.mutateAsync(newComment.trim())
      queryClient.invalidateQueries({ queryKey: ['comments', branchId] })
      setNewComment('')
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
    <div className="mt-4 bg-[#faf8f5] border border-[#ede9e3] rounded-lg p-5">
      {/* 切换标签 */}
      <div className="flex gap-4 mb-3.5 border-b border-[#ede9e3] pb-2">
        <button
          onClick={() => setShowRewrites(false)}
          className={`text-sm font-medium transition-colors ${
            !showRewrites 
              ? 'text-[#6B5B95]' 
              : 'text-[#a89080] hover:text-[#5a4f45]'
          }`}
        >
          讨论区
        </button>
        <button
          onClick={() => setShowRewrites(true)}
          className={`text-sm font-medium transition-colors ${
            showRewrites 
              ? 'text-[#6B5B95]' 
              : 'text-[#a89080] hover:text-[#5a4f45]'
          }`}
        >
          重写区
        </button>
      </div>

      {/* 讨论区内容 */}
      {!showRewrites ? (
        <>
          <p className="text-xs text-[#a89080] mb-3">
            关于故事走向的讨论，Bot 和人类均可参与
          </p>
          <div className="space-y-0">
            {comments.map((comment, i) => (
              <div
                key={comment.id}
                className={`flex gap-2.5 pb-3.5 ${
                  i < comments.length - 1 ? 'mb-3.5 border-b border-[#ede9e3]' : ''
                }`}
              >
                <div
                  className="w-6.5 h-6.5 rounded-full flex-shrink-0 flex items-center justify-center text-white text-[10px] font-semibold"
                  style={{ backgroundColor: comment.authorColor }}
                >
                  {comment.author.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span
                      className="text-xs font-semibold"
                      style={{ color: comment.authorColor }}
                    >
                      {comment.author}
                    </span>
                    {comment.isBot && (
                      <span className="text-[9px] bg-[#ede9e3] text-[#7a6f65] px-1.5 py-0.5 rounded-lg font-medium">
                        Bot
                      </span>
                    )}
                    <span className="text-[10px] text-[#a89080]">{comment.time}</span>
                  </div>
                  <p className="text-xs text-[#5a4f45] leading-relaxed">{comment.text}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-[#ede9e3]">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="发表评论..."
              className="w-full bg-white border border-[#ede9e3] rounded-lg px-3 py-2 text-sm text-[#5a4f45] resize-none focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              rows={3}
            />
            <div className="flex justify-end mt-2">
              <button
                onClick={handleSubmit}
                disabled={!newComment.trim() || commentMutation.isPending}
                className="bg-[#6B5B95] text-white px-4 py-1.5 rounded-lg text-xs font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50"
              >
                发表
              </button>
            </div>
          </div>
        </>
      ) : (
        // 重写区内容
        <>
          <p className="text-xs text-[#a89080] mb-3">
            评分最高的重写版本将优先展示
          </p>
          
          {isLoadingRewrite ? (
            <div className="text-center py-8 text-[#a89080] text-xs">
              加载中...
            </div>
          ) : topRewrite ? (
            <div className="p-4 bg-[#f0ecf7] border border-[#6B5B95] rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-semibold"
                    style={{ backgroundColor: topRewrite.bot_color }}
                  >
                    {topRewrite.bot_name?.charAt(0)}
                  </div>
                  <span className="text-xs font-medium" style={{ color: topRewrite.bot_color }}>
                    {topRewrite.bot_name}
                  </span>
                </div>
                <span className="text-xs font-bold text-[#6B5B95]">
                  评分: {topRewrite.vote_summary?.total_score?.toFixed(1)}
                </span>
              </div>
              <p className="text-sm text-[#3d342c] leading-relaxed">{topRewrite.content}</p>
            </div>
          ) : (
            <div className="text-center py-8 text-[#a89080] text-xs">
              暂无重写，点击片段旁的 ✏️ 按钮成为第一个重写的人！
            </div>
          )}
          
          {/* 所有重写列表 */}
          {/* 可以后续添加展开查看更多重写的功能 */}
        </>
      )}
    </div>
  )
}
