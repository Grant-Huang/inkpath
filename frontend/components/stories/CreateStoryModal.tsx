'use client'

import { useState, useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { storiesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface CreateStoryModalProps {
  onClose: () => void
}

interface UploadedFile {
  name: string
  content: string
}

export default function CreateStoryModal({ onClose }: CreateStoryModalProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState({
    title: '',
    background: '',
    style_rules: '',
    language: 'zh' as 'zh' | 'en',
  })
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const createStoryMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await storiesApi.create(data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      router.push(`/stories/${data.data.id}`)
      onClose()
    },
  })

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    const newFiles: UploadedFile[] = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      if (file.name.endsWith('.md')) {
        try {
          const content = await file.text()
          newFiles.push({ name: file.name, content })
        } catch (error) {
          console.error(`Failed to read file ${file.name}:`, error)
        }
      }
    }

    setUploadedFiles(prev => [...prev, ...newFiles])
    setIsUploading(false)
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.background.trim()) {
      alert('请填写故事标题和背景描述')
      return
    }

    // Build story package data from uploaded files
    const storyPackage: Record<string, string> = {}
    uploadedFiles.forEach(file => {
      // Extract number prefix from filename (e.g., "10_evidence_pack.md" -> "evidence_pack")
      const match = file.name.match(/^\d+_(.+)\.md$/)
      if (match) {
        storyPackage[match[1]] = file.content
      }
    })

    await createStoryMutation.mutateAsync({
      title: formData.title,
      background: formData.background,
      style_rules: formData.style_rules || undefined,
      language: formData.language,
      min_length: 150,
      max_length: 500,
      // Include story package files if any were uploaded
      ...(Object.keys(storyPackage).length > 0 && { story_package: storyPackage }),
    })
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg p-4 sm:p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl serif font-bold text-[#2c2420] mb-4">创建新故事</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* 故事标题 */}
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

            {/* 语言 */}
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">语言</label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value as 'zh' | 'en' })}
                className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                disabled={createStoryMutation.isPending}
              >
                <option value="zh">中文</option>
                <option value="en">英文</option>
              </select>
            </div>

            {/* 背景描述 */}
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

            {/* 故事包上传 */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-[#5a4f45]">
                  上传故事包（MD文件）<span className="text-xs text-[#a89080] font-normal">（强烈建议）</span>
                </label>
                <a
                  href="/docs/10_故事发起者帮助文档_人类版.md"
                  target="_blank"
                  className="text-xs text-[#6B5B95] hover:text-[#5a4a85] font-medium transition-colors flex items-center gap-1 underline"
                >
                  <span>📖</span>
                  <span>查看帮助</span>
                </a>
              </div>
              <div className="border-2 border-dashed border-[#d9d3ca] rounded-lg p-4">
                <div className="text-center">
                  <p className="text-xs text-[#7a6f65] mb-2">支持上传多个MD文件</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".md"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={isUploading || createStoryMutation.isPending}
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading || createStoryMutation.isPending}
                    className="bg-[#f5f2ef] border border-[#ede9e3] rounded-lg px-4 py-2 text-sm text-[#5a4f45] hover:bg-[#f0ecf7] hover:border-[#6B5B95] transition-colors disabled:opacity-50"
                  >
                    {isUploading ? '处理中...' : '选择文件'}
                  </button>
                  
                  {/* 已上传文件列表 */}
                  {uploadedFiles.length > 0 && (
                    <div id="story-pack-file-list" className="mt-3 text-left space-y-1">
                      {uploadedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-[#f5f2ef] rounded px-2 py-1 text-xs">
                          <span className="text-[#5a4f45] truncate max-w-[200px]">{file.name}</span>
                          <button
                            type="button"
                            onClick={() => removeFile(index)}
                            className="text-[#b8574e] hover:text-[#a04538] ml-2"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-2 text-xs text-[#a89080]">
                <p className="mb-1"><strong>故事包文件说明：</strong></p>
                <ul className="list-disc list-inside space-y-0.5 ml-2">
                  <li><code className="bg-[#f5f2ef] px-1 rounded">00_meta.md</code> - 故事元信息（必填）</li>
                  <li><code className="bg-[#f5f2ef] px-1 rounded">10_evidence_pack.md</code> - 证据包（强烈建议）</li>
                  <li><code className="bg-[#f5f2ef] px-1 rounded">20_stance_pack.md</code> - 立场包（强烈建议）</li>
                  <li><code className="bg-[#f5f2ef] px-1 rounded">30_cast.md</code> - 角色卡（建议）</li>
                  <li><code className="bg-[#f5f2ef] px-1 rounded">40_plot_outline.md</code> - 剧情大纲（建议）</li>
                  <li><code className="bg-[#f5f2ef] px-1 rounded">50_constraints.md</code> - 约束（建议）</li>
                  <li><code className="bg-[#f5f2ef] px-1 rounded">60_sources.md</code> - 来源清单（建议）</li>
                </ul>
              </div>
            </div>

            {/* 写作风格规范 */}
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
          </div>

          {/* 按钮 */}
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
        
        {/* 错误提示 */}
        {createStoryMutation.isError && (
          <div className="mt-4 text-sm text-red-600">
            创建失败：{createStoryMutation.error instanceof Error ? createStoryMutation.error.message : '未知错误'}
          </div>
        )}
      </div>
    </div>
  )
}
