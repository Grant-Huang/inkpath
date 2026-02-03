'use client'

import { useState, useRef, useEffect } from 'react'
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
      try {
        const content = await file.text()
        newFiles.push({ name: file.name, content })
      } catch (error) {
        console.error(`Failed to read file ${file.name}:`, error)
      }
    }

    setUploadedFiles(prev => [...prev, ...newFiles])
    setIsUploading(false)
    
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // 检查登录状态
    const token = localStorage.getItem('jwt_token')
    if (!token) {
      alert('请先登录再创建故事')
      router.push('/login')
      return
    }
    
    if (!formData.title.trim() || !formData.background.trim()) {
      alert('请填写故事标题和背景描述')
      return
    }

    const storyPackage: Record<string, any> = {}
    const requiredFiles = ['metadata.json', 'characters.json', 'outline.json']
    const uploadedNames = uploadedFiles.map(f => f.name)
    
    const missingRequired = requiredFiles.filter(f => !uploadedNames.includes(f))
    if (missingRequired.length > 0) {
      alert(`❌ 缺少必选文件：${missingRequired.join(', ')}`)
      return
    }

    for (const file of uploadedFiles) {
      try {
        if (file.name.endsWith('.json')) {
          storyPackage[file.name.replace('.json', '')] = JSON.parse(file.content)
        } else {
          storyPackage[file.name.replace('.md', '')] = file.content
        }
      } catch (error) {
        console.error(`Failed to parse file ${file.name}:`, error)
      }
    }

    await createStoryMutation.mutateAsync({
      title: formData.title,
      background: formData.background,
      style_rules: formData.style_rules || undefined,
      language: formData.language,
      min_length: 150,
      max_length: 500,
      ...(Object.keys(storyPackage).length > 0 && { story_package: storyPackage }),
    })
  }

  // 必选文件列表
  const requiredFiles = ['metadata.json', 'characters.json', 'outline.json']
  const recommendedFiles = ['first_chapter.md', 'worldbuilding.json', 'rules.json']
  const uploadedNames = uploadedFiles.map(f => f.name)

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg sm:rounded-xl w-full max-w-lg max-h-[95vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题区域 */}
        <div className="sticky top-0 bg-white sm:bg-transparent border-b border-[#ede9e3] px-4 py-3 sm:px-6 sm:py-4">
          <h2 className="text-lg sm:text-xl serif font-bold text-[#2c2420]">创建新故事</h2>
          <p className="hidden sm:block text-xs text-[#a89080] mt-1">创建属于你的协作故事</p>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4">
          {/* 故事标题 */}
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
              标题 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              placeholder="输入故事标题"
              required
              disabled={createStoryMutation.isPending}
            />
          </div>

          {/* 语言选择 */}
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">语言</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, language: 'zh' })}
                disabled={createStoryMutation.isPending}
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  formData.language === 'zh' 
                    ? 'bg-[#6B5B95] text-white' 
                    : 'bg-[#f5f2ef] text-[#5a4f45] border border-[#ede9e3]'
                }`}
              >
                中文
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, language: 'en' })}
                disabled={createStoryMutation.isPending}
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  formData.language === 'en' 
                    ? 'bg-[#6B5B95] text-white' 
                    : 'bg-[#f5f2ef] text-[#5a4f45] border border-[#ede9e3]'
                }`}
              >
                English
              </button>
            </div>
          </div>

          {/* 背景描述 */}
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
              背景 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.background}
              onChange={(e) => setFormData({ ...formData, background: e.target.value })}
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              rows={3}
              placeholder="描述故事的背景设定..."
              required
              disabled={createStoryMutation.isPending}
            />
          </div>

          {/* 故事包上传 - 移动端折叠 */}
          <details className="group">
            <summary className="flex items-center justify-between cursor-pointer list-none">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-[#5a4f45]">上传故事包</span>
                {/* 显示文件状态 */}
                <div className="flex gap-1">
                  {requiredFiles.map(file => (
                    <span 
                      key={file}
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        uploadedNames.includes(file) 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-50 text-red-600'
                      }`}
                    >
                      {file}
                    </span>
                  ))}
                </div>
              </div>
              <span className="text-xs text-[#a89080] group-open:rotate-180 transition-transform">▼</span>
            </summary>
            
            <div className="mt-3 space-y-3">
              {/* 上传区域 */}
              <div className="border-2 border-dashed border-[#d9d3ca] rounded-lg p-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".json,.md"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={isUploading || createStoryMutation.isPending}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading || createStoryMutation.isPending}
                  className="w-full bg-[#f5f2ef] border border-[#ede9e3] rounded-lg py-3 text-sm text-[#5a4f45] hover:bg-[#f0ecf7] hover:border-[#6B5B95] transition-colors disabled:opacity-50"
                >
                  {isUploading ? '处理中...' : '+ 选择文件'}
                </button>
                
                {/* 已上传文件 */}
                {uploadedFiles.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-[#f5f2ef] rounded px-2 py-1.5 text-xs">
                        <span className="text-[#5a4f45] truncate flex-1">{file.name}</span>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="text-[#b8574e] hover:text-[#a04538] ml-2 px-1"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 文件说明 - 折叠内 */}
              <div className="text-xs text-[#a89080] space-y-2">
                <p className="font-medium text-[#5a4f45]">📁 文件说明</p>
                
                <div className="grid sm:grid-cols-2 gap-2">
                  {/* 必选文件 */}
                  <div className="bg-red-50 rounded-lg p-2">
                    <p className="font-medium text-red-700 mb-1">❌ 必选（缺少无法创建）</p>
                    <ul className="space-y-0.5 text-[10px]">
                      {requiredFiles.map(file => (
                        <li key={file} className="flex items-center gap-1">
                          <span className={uploadedNames.includes(file) ? 'text-green-600' : 'text-red-500'}>
                            {uploadedNames.includes(file) ? '✓' : '○'}
                          </span>
                          {file}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {/* 推荐文件 */}
                  <div className="bg-purple-50 rounded-lg p-2">
                    <p className="font-medium text-purple-700 mb-1">✅ 推荐</p>
                    <ul className="space-y-0.5 text-[10px]">
                      {recommendedFiles.map(file => (
                        <li key={file} className="flex items-center gap-1">
                          <span className={uploadedNames.includes(file) ? 'text-green-600' : 'text-purple-500'}>
                            {uploadedNames.includes(file) ? '✓' : '○'}
                          </span>
                          {file}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                {/* 帮助链接 */}
                <a
                  href="/docs/10_故事发起者帮助文档_人类版.md"
                  target="_blank"
                  className="inline-flex items-center gap-1 text-[#6B5B95] hover:text-[#5a4a85] underline"
                >
                  📖 查看帮助文档
                </a>
              </div>
            </div>
          </details>

          {/* 写作风格 - 可选折叠 */}
          <details className="group">
            <summary className="flex items-center justify-between cursor-pointer list-none py-2">
              <span className="text-sm font-medium text-[#5a4f45]">写作风格（可选）</span>
              <span className="text-xs text-[#a89080] group-open:rotate-180 transition-transform">▼</span>
            </summary>
            <textarea
              value={formData.style_rules}
              onChange={(e) => setFormData({ ...formData, style_rules: e.target.value })}
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              rows={2}
              placeholder="例如：第三人称视角，注重心理描写..."
              disabled={createStoryMutation.isPending}
            />
          </details>

          {/* 按钮 */}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={createStoryMutation.isPending}
              className="flex-1 border border-[#ede9e3] rounded-lg py-2.5 text-sm text-[#5a4f45] hover:bg-[#faf8f5] transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createStoryMutation.isPending}
              className="flex-1 bg-[#6B5B95] text-white rounded-lg py-2.5 text-sm font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createStoryMutation.isPending ? '创建中...' : '创建故事'}
            </button>
          </div>
        </form>
        
        {/* 错误提示 */}
        {createStoryMutation.isError && (
          <div className="px-4 pb-4 text-sm text-red-600">
            创建失败：{createStoryMutation.error instanceof Error ? createStoryMutation.error.message : '未知错误'}
          </div>
        )}
      </div>
    </div>
  )
}
