'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { storiesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface CreateStoryModalProps {
  onClose: () => void
}

export default function CreateStoryModal({ onClose }: CreateStoryModalProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    title: '',
    background: '',
    style_rules: '',
    language: 'zh' as 'zh' | 'en',
  })

  const createStoryMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await storiesApi.create(data)
      return response.data
    },
    onSuccess: (data) => {
      // 刷新故事列表
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      // 跳转到新创建的故事
      router.push(`/components/stories/${data.data.id}`)
      onClose()
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.background.trim()) {
      alert('请填写故事标题和背景描述')
      return
    }

    await createStoryMutation.mutateAsync({
      title: formData.title,
      background: formData.background,
      style_rules: formData.style_rules || undefined,
      language: formData.language,
      min_length: 150,
      max_length: 500,
    })
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl serif font-bold text-[#2c2420] mb-4">创建新故事</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                故事标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                placeholder="输入故事标题"
                required
                disabled={createStoryMutation.isPending}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                背景描述 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.background}
                onChange={(e) => setFormData({ ...formData, background: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                rows={4}
                placeholder="描述故事的背景设定..."
                required
                disabled={createStoryMutation.isPending}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                写作风格规范（可选）
              </label>
              <textarea
                value={formData.style_rules}
                onChange={(e) => setFormData({ ...formData, style_rules: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                rows={3}
                placeholder="例如：第三人称视角，注重心理描写..."
                disabled={createStoryMutation.isPending}
              />
            </div>
            <div className="flex gap-2 items-center">
              <label className="block text-sm font-medium text-[#5a4f45]">语言</label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value as 'zh' | 'en' })}
                className="border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95]"
                disabled={createStoryMutation.isPending}
              >
                <option value="zh">中文</option>
                <option value="en">英文</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={createStoryMutation.isPending}
              className="flex-1 border border-[#ede9e3] rounded-lg px-4 py-2 text-sm text-[#5a4f45] hover:bg-[#faf8f5] transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createStoryMutation.isPending}
              className="flex-1 bg-[#6B5B95] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createStoryMutation.isPending ? '创建中...' : '创建'}
            </button>
          </div>
        </form>
        {createStoryMutation.isError && (
          <div className="mt-4 text-sm text-red-600">
            创建失败：{createStoryMutation.error instanceof Error ? createStoryMutation.error.message : '未知错误'}
          </div>
        )}
      </div>
    </div>
  )
}
