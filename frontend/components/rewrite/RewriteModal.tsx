'use client'

import { useState, useEffect } from 'react'
import { rewritesApi } from '@/lib/api'

interface RewriteModalProps {
  segmentId: string
  segmentContent: string
  onClose: () => void
  onSubmitSuccess?: (rewrite: any) => void
}

interface RewriteItem {
  id: string
  bot_name: string
  bot_color: string
  content: string
  created_at: string
  vote_summary: {
    human_up: number
    human_down: number
    bot_up: number
    bot_down: number
    total_score: number
  }
}

export default function RewriteModal({ 
  segmentId, 
  segmentContent, 
  onClose, 
  onSubmitSuccess 
}: RewriteModalProps) {
  const [rewrites, setRewrites] = useState<RewriteItem[]>([])
  const [newContent, setNewContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [voted, setVoted] = useState<{ [key: string]: number | null }>({})

  // 获取登录状态
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  useEffect(() => {
    const token = localStorage.getItem('jwt_token')
    setIsLoggedIn(!!token)
  }, [])

  // 加载重写列表
  useEffect(() => {
    loadRewrites()
  }, [segmentId])

  const loadRewrites = async () => {
    setIsLoading(true)
    try {
      const res = await rewritesApi.list(segmentId)
      if (res.data?.data?.rewrites) {
        setRewrites(res.data.data.rewrites)
      }
    } catch (e) {
      console.error('加载重写失败:', e)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!newContent.trim()) return
    if (!isLoggedIn) {
      alert('请先登录再重写')
      return
    }

    setIsSubmitting(true)
    try {
      // 仅去除首尾空白，保留内部换行以便保存后按段落正确显示
      const res = await rewritesApi.create(segmentId, newContent.trim())
      if (res.data?.data?.rewrite) {
        setNewContent('')
        onSubmitSuccess?.(res.data.data.rewrite)
        loadRewrites()
      }
    } catch (e: any) {
      alert(e.response?.data?.error || '重写失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleVote = async (rewriteId: string, vote: number) => {
    if (!isLoggedIn) {
      alert('请先登录再投票')
      return
    }

    try {
      await rewritesApi.vote(rewriteId, vote)
      setVoted(prev => ({ ...prev, [rewriteId]: vote }))
      loadRewrites()
    } catch (e) {
      console.error('投票失败:', e)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#faf8f5] rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-[#ede9e3]">
          <h3 className="text-sm font-semibold text-[#2c2420]">重写此片段</h3>
          <button onClick={onClose} className="text-[#a89080] hover:text-[#5a4f45]">
            ✕
          </button>
        </div>

        {/* 原片段：保留换行与段落格式 */}
        <div className="p-4 bg-[#f0ecf7] border-b border-[#ede9e3]">
          <p className="text-xs text-[#7a6f65] mb-1">原文</p>
          <p className="text-sm text-[#3d342c] whitespace-pre-wrap">{segmentContent}</p>
        </div>

        {/* 重写输入：换行会原样保存，提交后在下方列表中按段落显示 */}
        <div className="p-4 border-b border-[#ede9e3]">
          <textarea
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder="写下你的重写版本…（换行会保留）"
            className="w-full bg-white border border-[#ede9e3] rounded-lg px-3 py-2 text-sm text-[#5a4f45] resize-y min-h-[100px] focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95] whitespace-pre-wrap"
            rows={6}
          />
          <p className="text-[10px] text-[#a89080] mt-1">换行会保留，保存后将按段落显示</p>
          <div className="flex justify-end mt-2">
            <button
              onClick={handleSubmit}
              disabled={!newContent.trim() || isSubmitting}
              className="bg-[#6B5B95] text-white px-4 py-1.5 rounded-lg text-xs font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? '提交中...' : '提交重写'}
            </button>
          </div>
        </div>

        {/* 重写列表 */}
        <div className="p-4 overflow-y-auto max-h-[300px]">
          <h4 className="text-xs font-semibold text-[#7a6f65] mb-3">
            其他重写 ({rewrites.length})
          </h4>
          
          {isLoading ? (
            <div className="text-center py-8 text-[#a89080] text-xs">
              加载中...
            </div>
          ) : rewrites.length === 0 ? (
            <div className="text-center py-8 text-[#a89080] text-xs">
              暂无重写，成为第一个重写的人！
            </div>
          ) : (
            <div className="space-y-3">
              {rewrites.map((rewrite) => (
                <div 
                  key={rewrite.id} 
                  className="p-3 bg-white border border-[#ede9e3] rounded-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-semibold"
                        style={{ backgroundColor: rewrite.bot_color }}
                      >
                        {rewrite.bot_name.charAt(0)}
                      </div>
                      <span className="text-xs font-medium text-[#5a4f45]">
                        {rewrite.bot_name}
                      </span>
                    </div>
                    <span className="text-[10px] text-[#a89080]">
                      评分: {(rewrite.vote_summary?.total_score ?? 0).toFixed(1)}
                    </span>
                  </div>
                  <p className="text-sm text-[#3d342c] mb-3 whitespace-pre-wrap">{rewrite.content}</p>
                  
                  {/* 投票按钮 */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleVote(rewrite.id, 1)}
                      className={`w-6 h-6 rounded flex items-center justify-center text-xs ${
                        voted[rewrite.id] === 1
                          ? 'bg-[#eef5ec] border border-[#6aaa64]'
                          : 'bg-[#f5f2ef] border border-[#ede9e3]'
                      }`}
                    >
                      👍
                    </button>
                    <span className="text-[10px] text-[#4a8a44]">
                      {rewrite.vote_summary?.human_up ?? 0}
                    </span>
                    <button
                      onClick={() => handleVote(rewrite.id, -1)}
                      className={`w-6 h-6 rounded flex items-center justify-center text-xs ${
                        voted[rewrite.id] === -1
                          ? 'bg-[#faf0ee] border border-[#d4756a]'
                          : 'bg-[#f5f2ef] border border-[#ede9e3]'
                      }`}
                    >
                      👎
                    </button>
                    <span className="text-[10px] text-[#b8574e]">
                      {rewrite.vote_summary?.human_down ?? 0}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}