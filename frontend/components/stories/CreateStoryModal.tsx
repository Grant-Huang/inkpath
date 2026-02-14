'use client'

import { useState, useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { storiesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface CreateStoryModalProps {
  onClose: () => void
}

// 故事包文件配置
interface StoryPackFile {
  key: string  // 文件key，用于API提交
  filename: string  // 显示的文件名
  displayName: string  // 中文显示名称
  required: boolean  // 是否必填
  acceptedExt: string[]  // 接受的文件扩展名
  helpUrl?: string  // 帮助文档链接
  description: string  // 文件说明
}

const STORY_PACK_FILES: StoryPackFile[] = [
  {
    key: 'meta',
    filename: '00_meta.md',
    displayName: '故事元信息',
    required: true,
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/00_meta',
    description: '故事的基本信息（标题、时代、类型等）'
  },
  {
    key: 'evidence_pack',
    filename: '10_evidence_pack.md',
    displayName: '证据包',
    required: true,
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/10_evidence_pack',
    description: '提供"第1层残篇"，决定历史感 ⭐ 最重要'
  },
  {
    key: 'stance_pack',
    filename: '20_stance_pack.md',
    displayName: '立场包',
    required: true,
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/20_stance_pack',
    description: '提供"第2层立场"，决定冲突 ⭐ 最重要'
  },
  {
    key: 'cast',
    filename: '30_cast.md',
    displayName: '角色卡',
    required: true,  // ⭐ 改为必填
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/30_cast',
    description: '提供"第3层个体"，决定拼图 ⭐ 必填'
  },
  {
    key: 'starter',
    filename: '70_Starter.md',
    displayName: '开篇',
    required: true,  // ⭐ 新增必填
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/70_starter',
    description: '故事开篇（2000-3000字），设定基调、引出主角 ⭐ 必填'
  },
  {
    key: 'plot_outline',
    filename: '40_plot_outline.md',
    displayName: '剧情大纲',
    required: false,
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/40_plot_outline',
    description: '信息流大纲（不是三幕结构）'
  },
  {
    key: 'constraints',
    filename: '50_constraints.md',
    displayName: '约束与边界',
    required: false,
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/50_constraints',
    description: '硬约束、软约束、内容边界'
  },
  {
    key: 'sources',
    filename: '60_sources.md',
    displayName: '来源清单',
    required: false,
    acceptedExt: ['.md'],
    helpUrl: 'https://docs.inkpath.cc/templates/60_sources',
    description: '可追溯性'
  }
]

interface UploadedFile {
  key: string
  filename: string
  content: string
  valid: boolean
  errorMessage?: string
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
  const [uploadedFiles, setUploadedFiles] = useState<Map<string, UploadedFile>>(new Map())
  const [currentUploadKey, setCurrentUploadKey] = useState<string | null>(null)

  const createStoryMutation = useMutation({
    mutationFn: async (payload: any) => {
      const response = await storiesApi.create(payload)
      const body = response.data as { status?: string; data?: { id: string }; error?: { message?: string } }
      if (response.status >= 400 || body?.status === 'error') {
        const msg = body?.error?.message || (response.status === 401 ? '登录已过期或未登录，请重新登录' : `请求失败 (${response.status})`)
        throw new Error(msg)
      }
      return body
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      const id = data?.data?.id
      if (id) {
        router.push(`/stories/${id}`)
      }
      onClose()
    },
    onError: (error: Error) => {
      const msg = error.message || ''
      if (msg.includes('登录') || msg.includes('认证') || msg.includes('Token') || msg.includes('401')) {
        localStorage.removeItem('jwt_token')
        alert(msg + '\n\n请重新登录后再创建故事。')
        router.push('/login')
      }
    },
  })

  // 验证MD文件格式
  const validateMarkdownFile = (content: string, fileConfig: StoryPackFile): { valid: boolean; error?: string } => {
    if (!content || content.trim().length === 0) {
      return { valid: false, error: '文件内容为空' }
    }

    // 检查是否有Markdown前置元数据（YAML front matter）
    if (fileConfig.key === 'meta') {
      if (!content.startsWith('---')) {
        return { valid: false, error: '缺少YAML前置元数据（应以 --- 开头）' }
      }
      const yamlEndIndex = content.indexOf('---', 3)
      if (yamlEndIndex === -1) {
        return { valid: false, error: '前置元数据格式不完整（缺少结束的 ---）' }
      }
      
      // 检查必要的元数据字段
      const yamlContent = content.substring(3, yamlEndIndex)
      const requiredFields = ['pack_id', 'title', 'logline', 'era']
      for (const field of requiredFields) {
        if (!yamlContent.includes(`${field}:`)) {
          return { valid: false, error: `缺少必要字段: ${field}` }
        }
      }
    }

    // 检查是否有Markdown标题（至少有一个 # 开头的行）
    const lines = content.split('\n')
    const hasHeading = lines.some(line => line.trim().startsWith('#'))
    if (!hasHeading) {
      return { valid: false, error: '文件缺少Markdown标题（建议使用 # ## ### 等）' }
    }

    // 检查最小长度
    if (content.length < 50) {
      return { valid: false, error: '文件内容过短（至少50字符）' }
    }

    return { valid: true }
  }

  // 处理文件上传
  const handleFileUpload = async (fileConfig: StoryPackFile, file: File) => {
    // 检查文件扩展名
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!fileConfig.acceptedExt.includes(fileExt)) {
      alert(`❌ 文件格式错误\n\n期望：${fileConfig.acceptedExt.join(' 或 ')}\n实际：${fileExt}`)
      return
    }

    try {
      const content = await file.text()
      
      // 验证文件格式
      const validation = validateMarkdownFile(content, fileConfig)
      
      const uploadedFile: UploadedFile = {
        key: fileConfig.key,
        filename: file.name,
        content: content,
        valid: validation.valid,
        errorMessage: validation.error
      }

      setUploadedFiles(prev => {
        const newMap = new Map(prev)
        newMap.set(fileConfig.key, uploadedFile)
        return newMap
      })

      if (!validation.valid) {
        alert(`⚠️ 文件验证警告\n\n文件：${file.name}\n问题：${validation.error}\n\n您可以继续上传其他文件，但建议修复此问题后重新上传。`)
      }
    } catch (error) {
      console.error(`Failed to read file ${file.name}:`, error)
      alert(`❌ 文件读取失败：${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  // 移除已上传的文件
  const removeFile = (key: string) => {
    setUploadedFiles(prev => {
      const newMap = new Map(prev)
      newMap.delete(key)
      return newMap
    })
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

    // 检查必填文件
    const requiredFiles = STORY_PACK_FILES.filter(f => f.required)
    const missingRequired = requiredFiles.filter(f => !uploadedFiles.has(f.key))
    if (missingRequired.length > 0) {
      alert(`❌ 缺少必填文件：\n\n${missingRequired.map(f => `• ${f.displayName} (${f.filename})`).join('\n')}\n\n请上传这些文件后再提交。`)
      return
    }

    // 检查是否有验证失败的文件
    const invalidFiles = Array.from(uploadedFiles.values()).filter(f => !f.valid)
    if (invalidFiles.length > 0) {
      const confirmSubmit = confirm(
        `⚠️ 有 ${invalidFiles.length} 个文件验证失败：\n\n${invalidFiles.map(f => `• ${f.filename}: ${f.errorMessage}`).join('\n')}\n\n是否仍要继续提交？`
      )
      if (!confirmSubmit) {
        return
      }
    }

    // 构建故事包数据
    const storyPackage: Record<string, string> = {}
    uploadedFiles.forEach((file, key) => {
      storyPackage[key] = file.content
    })

    await createStoryMutation.mutateAsync({
      title: formData.title,
      background: formData.background,
      style_rules: formData.style_rules || undefined,
      language: formData.language,
      min_length: 150,
      max_length: 500,
      ...(Object.keys(storyPackage).length > 0 && { story_pack: storyPackage }),
    })
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg sm:rounded-xl w-full max-w-2xl max-h-[95vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题区域 */}
        <div className="sticky top-0 bg-white border-b border-[#ede9e3] px-4 py-3 sm:px-6 sm:py-4 z-10">
          <h2 className="text-lg sm:text-xl serif font-bold text-[#2c2420]">创建新故事</h2>
          <p className="text-xs text-[#a89080] mt-1">填写基本信息并上传故事包</p>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-5">
          {/* 故事标题 */}
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
              故事标题 <span className="text-red-500">*</span>
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
              背景描述 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.background}
              onChange={(e) => setFormData({ ...formData, background: e.target.value })}
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              rows={3}
              placeholder="简要描述故事的背景设定..."
              required
              disabled={createStoryMutation.isPending}
            />
          </div>

          {/* 写作风格 - 可选 */}
          <details className="group">
            <summary className="flex items-center justify-between cursor-pointer list-none py-2">
              <span className="text-sm font-medium text-[#5a4f45]">写作风格（可选）</span>
              <span className="text-xs text-[#a89080] group-open:rotate-180 transition-transform">▼</span>
            </summary>
            <textarea
              value={formData.style_rules}
              onChange={(e) => setFormData({ ...formData, style_rules: e.target.value })}
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95] mt-2"
              rows={2}
              placeholder="例如：第三人称视角，注重心理描写..."
              disabled={createStoryMutation.isPending}
            />
          </details>

          {/* 故事包上传区域 */}
          <div className="border-t border-[#ede9e3] pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-[#5a4f45]">故事包文件</h3>
              <a
                href="https://docs.inkpath.cc/guide/story-creator"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[#6B5B95] hover:text-[#5a4a85] underline flex items-center gap-1"
              >
                📖 查看完整帮助文档
              </a>
            </div>

            <div className="space-y-2">
              {STORY_PACK_FILES.map((fileConfig) => {
                const uploaded = uploadedFiles.get(fileConfig.key)
                const isUploaded = !!uploaded
                
                return (
                  <div
                    key={fileConfig.key}
                    className={`border rounded-lg p-3 ${
                      isUploaded
                        ? uploaded.valid
                          ? 'border-green-300 bg-green-50'
                          : 'border-yellow-300 bg-yellow-50'
                        : fileConfig.required
                        ? 'border-red-200 bg-red-50'
                        : 'border-[#ede9e3] bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-medium ${
                            fileConfig.required ? 'text-red-600' : 'text-purple-600'
                          }`}>
                            {fileConfig.required ? '必填' : '推荐'}
                          </span>
                          <span className="text-sm font-medium text-[#2c2420]">
                            {fileConfig.displayName}
                          </span>
                          {isUploaded && (
                            <span className="text-xs">
                              {uploaded.valid ? '✓' : '⚠️'}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-[#7a6f65] mb-1">{fileConfig.description}</p>
                        <p className="text-xs text-[#a89080]">
                          文件名：<code className="bg-white px-1 py-0.5 rounded">{fileConfig.filename}</code>
                        </p>
                        
                        {isUploaded && (
                          <div className="mt-2 text-xs">
                            {uploaded.valid ? (
                              <span className="text-green-700">✓ 已上传并通过验证</span>
                            ) : (
                              <span className="text-yellow-700">⚠️ {uploaded.errorMessage}</span>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col gap-1">
                        {!isUploaded ? (
                          <label
                            className="px-3 py-1.5 bg-[#6B5B95] text-white text-xs rounded cursor-pointer hover:bg-[#5a4a85] transition-colors text-center whitespace-nowrap"
                          >
                            上传
                            <input
                              type="file"
                              accept={fileConfig.acceptedExt.join(',')}
                              onChange={(e) => {
                                const file = e.target.files?.[0]
                                if (file) {
                                  handleFileUpload(fileConfig, file)
                                }
                                e.target.value = '' // 重置input
                              }}
                              className="hidden"
                              disabled={createStoryMutation.isPending}
                            />
                          </label>
                        ) : (
                          <>
                            <label
                              className="px-3 py-1.5 bg-[#f5f2ef] border border-[#ede9e3] text-[#5a4f45] text-xs rounded cursor-pointer hover:bg-[#ede9e3] transition-colors text-center whitespace-nowrap"
                            >
                              重新上传
                              <input
                                type="file"
                                accept={fileConfig.acceptedExt.join(',')}
                                onChange={(e) => {
                                  const file = e.target.files?.[0]
                                  if (file) {
                                    handleFileUpload(fileConfig, file)
                                  }
                                  e.target.value = ''
                                }}
                                className="hidden"
                                disabled={createStoryMutation.isPending}
                              />
                            </label>
                            <button
                              type="button"
                              onClick={() => removeFile(fileConfig.key)}
                              className="px-3 py-1.5 text-xs text-[#b8574e] hover:text-[#a04538] border border-[#ede9e3] rounded hover:bg-red-50 transition-colors"
                              disabled={createStoryMutation.isPending}
                            >
                              删除
                            </button>
                          </>
                        )}
                        
                        {fileConfig.helpUrl && (
                          <a
                            href={fileConfig.helpUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 text-xs text-[#6B5B95] hover:text-[#5a4a85] underline text-center"
                          >
                            查看模板
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* 上传进度提示 */}
            <div className="mt-3 p-3 bg-[#f5f2ef] rounded-lg">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#5a4f45]">
                  已上传：{uploadedFiles.size} / {STORY_PACK_FILES.filter(f => f.required).length} 必填 + {STORY_PACK_FILES.filter(f => !f.required).length} 推荐
                </span>
                <span className={`font-medium ${
                  uploadedFiles.size >= STORY_PACK_FILES.filter(f => f.required).length
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}>
                  {uploadedFiles.size >= STORY_PACK_FILES.filter(f => f.required).length ? '✓ 可以提交' : '✗ 缺少必填文件'}
                </span>
              </div>
            </div>
          </div>

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
              disabled={createStoryMutation.isPending || uploadedFiles.size < STORY_PACK_FILES.filter(f => f.required).length}
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
