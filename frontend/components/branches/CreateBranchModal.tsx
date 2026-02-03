'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { branchesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface CreateBranchModalProps {
  onClose: () => void
  storyId: string
  segmentId?: string | null
  branchId?: string
}

export default function CreateBranchModal({ 
  onClose, 
  storyId,
  segmentId,
  branchId
}: CreateBranchModalProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    initial_segment: '',
  })

  const createBranchMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await branchesApi.create(storyId, data)
      return response.data
    },
    onSuccess: (data) => {
      // 刷新分支列表
      queryClient.invalidateQueries({ queryKey: ['branches', storyId] })
      // 刷新续写段列表
      if (data.data?.id) {
        queryClient.invalidateQueries({ queryKey: ['segments', data.data.id] })
      }
      onClose()
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim()) {
      alert('请填写分支标题')
      return
    }

    if (!formData.initial_segment.trim()) {
      alert('请填写第一段续写内容')
      return
    }

    await createBranchMutation.mutateAsync({
      title: formData.title,
      description: formData.description || undefined,
      fork_at_segment_id: segmentId || undefined,
      parent_branch_id: branchId || undefined,
      initial_segment: formData.initial_segment,
    })
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl serif font-bold text-[#2c2420] mb-4">创建新分支</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                分支标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                placeholder="输入分支标题"
                required
                disabled={createBranchMutation.isPending}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                分支理由
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                rows={3}
                placeholder="说明为什么要创建这个分支..."
                disabled={createBranchMutation.isPending}
              />
            </div>
            {segmentId && (
              <div>
                <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                  从续写段分叉
                </label>
                <input
                  type="text"
                  value={`续写段 ${segmentId}`}
                  className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm bg-[#faf8f5] cursor-not-allowed"
                  readOnly
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                第一段续写（展示方向） <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.initial_segment}
                onChange={(e) => setFormData({ ...formData, initial_segment: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                rows={4}
                placeholder="作为创建者，你需要先写第一段来展示这个分支的方向..."
                required
                disabled={createBranchMutation.isPending}
              />
            </div>
          </div>
          <div className="flex gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={createBranchMutation.isPending}
              className="flex-1 border border-[#ede9e3] rounded-lg px-4 py-2 text-sm text-[#5a4f45] hover:bg-[#faf8f5] transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createBranchMutation.isPending}
              className="flex-1 bg-[#6B5B95] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createBranchMutation.isPending ? '创建中...' : '创建'}
            </button>
          </div>
        </form>
        {createBranchMutation.isError && (
          <div className="mt-4 text-sm text-red-600">
            创建失败：{createBranchMutation.error instanceof Error ? createBranchMutation.error.message : '未知错误'}
          </div>
        )}
      </div>
    </div>
  )
}
