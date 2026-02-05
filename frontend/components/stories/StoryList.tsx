'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Story } from '@/lib/types';
import { useStoryPrefetch } from '@/hooks/useStoryPrefetch';
import { useDebounce } from '@/hooks/useDebounce';

// 懒加载
const CreateStoryModal = dynamic(
  () => import('./CreateStoryModal'),
  { ssr: false }
);

interface StoryListProps {
  stories?: Story[];
  isLoading?: boolean;
}

interface StoryListItem {
  id: string;
  title: string;
  background?: string;
  language?: string;
  branches_count?: number;
  bots_count?: number;
  created_at?: string;
  min_length?: number;
  max_length?: number;
  owner_id?: string;
  owner_type?: string;
  status?: string;
}

interface DisplayStory {
  id: string;
  title: string;
  genre: string;
  branches: number;
  activeBots: number;
  lastUpdate: string;
  summary: string;
}

interface Participant {
  id: string;
  name: string;
  type: 'bot' | 'human';
  role: string;
  model?: string;
}

export default function StoryList({ stories = [], isLoading = false }: StoryListProps) {
  const router = useRouter();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { prefetchStory } = useStoryPrefetch();
  const [expandedStory, setExpandedStory] = useState<string | null>(null);
  const [participantsPopup, setParticipantsPopup] = useState<{
    show: boolean;
    storyId: string;
    storyTitle: string;
    participants: Participant[];
    loading: boolean;
  }>({
    show: false,
    storyId: '',
    storyTitle: '',
    participants: [],
    loading: false
  });

  const debouncedPrefetch = useDebounce((storyId: string) => {
    prefetchStory(storyId)
  }, 200)

  const handleStorySelect = (storyId: string) => {
    router.push(`/stories/${storyId}`)
  }

  const handleMouseEnter = (storyId: string) => {
    debouncedPrefetch(storyId)
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return '刚才'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  const formatStoryForDisplay = (story: StoryListItem): DisplayStory => {
    const background = story.background || ''
    return {
      id: story.id,
      title: story.title,
      genre: '', // 移除硬编码的类型，数据库中没有genre字段
      branches: story.branches_count || 0,
      activeBots: story.bots_count || 0,
      lastUpdate: formatTime(story.created_at || ''),
      summary: background.substring(0, 150) || '',
    }
  }

  // 获取所有分支的参与者（用于故事）
  const fetchStoryParticipants = async (storyId: string, storyTitle: string) => {
    setParticipantsPopup({
      show: true,
      storyId,
      storyTitle,
      participants: [],
      loading: true
    })

    try {
      // 获取故事的所有分支
      const branchesRes = await fetch(`https://inkpath-api.onrender.com/api/v1/stories/${storyId}/branches?limit=100`)
      const branchesData = await branchesRes.json()
      
      if (branchesData.status !== 'success') {
        throw new Error('获取分支失败')
      }

      const branches = branchesData.data.branches || []
      const allParticipants: Participant[] = []
      const participantIds = new Set<string>()

      // 获取每个分支的参与者
      for (const branch of branches) {
        try {
          const participantsRes = await fetch(`https://inkpath-api.onrender.com/api/v1/branches/${branch.id}/participants`)
          const participantsData = await participantsRes.json()
          
          if (participantsData.status === 'success') {
            for (const p of (participantsData.data.participants || [])) {
              if (!participantIds.has(p.id)) {
                participantIds.add(p.id)
                allParticipants.push(p)
              }
            }
          }
        } catch {
          // 忽略单个分支的错误
        }
      }

      setParticipantsPopup(prev => ({
        ...prev,
        participants: allParticipants,
        loading: false
      }))
    } catch (error) {
      console.error('获取参与者失败:', error)
      setParticipantsPopup(prev => ({
        ...prev,
        loading: false
      }))
    }
  }

  const closeParticipantsPopup = () => {
    setParticipantsPopup(prev => ({ ...prev, show: false }))
  }

  // =====================
  // 移动端布局
  // =====================
  return (
    <div className="lg:max-w-2xl lg:mx-auto lg:px-6 lg:py-12">
      
      {/* ===================== */}
      {/* 桌面端：保持原布局 */}
      {/* ===================== */}
      <div className="hidden lg:block">
        <div className="mb-10">
          <h1 className="text-3xl serif font-bold text-[#2c2420] mb-2 tracking-tight">
            故事库
          </h1>
          <p className="text-sm text-[#a89080]">
            AI 协作续写正在进行中的故事
          </p>
        </div>

        <div className="space-y-0.5">
          {(stories.length > 0 ? stories : []).map((story: StoryListItem) => {
            const display = formatStoryForDisplay(story)
            return (
              <div
                key={story.id}
                onClick={() => handleStorySelect(story.id)}
                onMouseEnter={() => handleMouseEnter(story.id)}
                className="bg-white border border-[#ede9e3] rounded-lg p-6 cursor-pointer transition-all duration-200 hover:border-[#6B5B95] hover:shadow-lg hover:shadow-[#6B5B95]/8"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 max-w-[520px]">
                    <div className="flex items-center gap-2.5 mb-1.5">
                      {display.genre && (
                        <span className="text-xs font-medium text-[#6B5B95] bg-[#f0ecf7] px-2.5 py-0.5 rounded-full tracking-wide">
                          {display.genre}
                        </span>
                      )}
                      <span className="text-xs text-[#a89080]">{display.lastUpdate}</span>
                    </div>
                    <h2 className="text-xl serif font-semibold text-[#2c2420] mb-1 tracking-tight">
                      {display.title}
                    </h2>
                    <p className="text-sm text-[#7a6f65] mb-2.5 leading-relaxed">
                      {display.summary}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-2 ml-6">
                    <div className="text-xs text-[#a89080]">
                      <span className="text-[#6B5B95] font-semibold">{display.branches}</span> 条分支
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        fetchStoryParticipants(story.id, story.title)
                      }}
                      className="text-xs text-[#a89080] mt-0.5 hover:text-[#6B5B95] transition-colors"
                    >
                      <span className="text-[#6B5B95] font-semibold">{display.activeBots}</span> 个 Bot
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
          
          {stories.length === 0 && (
            <div className="text-center py-12 text-[#a89080]">
              暂无故事，成为第一个创建者！
            </div>
          )}
        </div>

        <div
          onClick={() => setShowCreateModal(true)}
          className="mt-8 p-5 border-2 border-dashed border-[#d9d3ca] rounded-lg text-center cursor-pointer transition-all duration-150 hover:border-[#6B5B95]"
        >
          <span className="text-sm text-[#a89080]">+ 创建新故事</span>
        </div>
      </div>

      {/* ===================== */}
      {/* 移动端：折叠布局 */}
      {/* ===================== */}
      <div className="lg:hidden px-4 py-6">
        {/* 标题 */}
        <div className="mb-4">
          <h1 className="text-xl serif font-bold text-[#2c2420]">故事库</h1>
          <p className="text-xs text-[#a89080]">协作续写中</p>
        </div>

        {/* 故事列表 */}
        <div className="space-y-3">
          {(stories.length > 0 ? stories : []).map((story) => {
            const display = formatStoryForDisplay(story)
            const isExpanded = expandedStory === story.id
            
            return (
              <div key={story.id}>
                {/* 故事卡片 */}
                <div
                  onClick={() => setExpandedStory(isExpanded ? null : story.id)}
                  className="bg-white border border-[#ede9e3] rounded-lg p-4"
                >
                  {/* 标题行 */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {display.genre && (
                        <span className="text-xs font-medium text-[#6B5B95] bg-[#f0ecf7] px-2 py-0.5 rounded-full">
                          {display.genre}
                        </span>
                      )}
                      <span className="text-xs text-[#a89080]">{display.lastUpdate}</span>
                    </div>
                    <span className={`text-xs text-[#a89080] transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </div>
                  
                  {/* 标题 */}
                  <h2 className="text-base font-semibold text-[#2c2420] mt-2">
                    {display.title}
                  </h2>
                  
                  {/* 统计 */}
                  <div className="flex items-center gap-3 mt-2 text-xs text-[#a89080]">
                    <span>{display.branches} 分支</span>
                    <span>{display.activeBots} Bot</span>
                  </div>
                </div>

                {/* 展开内容 */}
                {isExpanded && (
                  <div className="mt-2 px-4 py-3 bg-[#faf8f5] rounded-lg">
                    <p className="text-xs text-[#7a6f65] leading-relaxed">
                      {display.summary}
                    </p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleStorySelect(story.id)
                      }}
                      className="mt-3 w-full py-2 bg-[#6B5B95] text-white rounded-lg text-xs font-medium"
                    >
                      进入故事 →
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* 创建按钮 */}
        <button
          onClick={() => setShowCreateModal(true)}
          className="mt-6 w-full py-3 border-2 border-dashed border-[#d9d3ca] rounded-lg text-sm text-[#a89080]"
        >
          + 创建新故事
        </button>
      </div>

      {/* 创建弹窗 */}
      {showCreateModal && (
        <CreateStoryModal onClose={() => setShowCreateModal(false)} />
      )}

      {/* 参与者弹窗 */}
      {participantsPopup.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={closeParticipantsPopup}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            {/* 头部 */}
            <div className="flex items-center justify-between p-4 border-b border-[#ede9e3]">
              <h3 className="font-semibold text-[#2c2420]">
                {participantsPopup.storyTitle} - 参与者
              </h3>
              <button onClick={closeParticipantsPopup} className="text-[#a89080] hover:text-[#2c2420]">
                ✕
              </button>
            </div>
            
            {/* 内容 */}
            <div className="p-4 max-h-[60vh] overflow-y-auto">
              {participantsPopup.loading ? (
                <div className="text-center py-8 text-[#a89080]">
                  加载中...
                </div>
              ) : participantsPopup.participants.length === 0 ? (
                <div className="text-center py-8 text-[#a89080]">
                  暂无参与者
                </div>
              ) : (
                <div className="space-y-2">
                  {participantsPopup.participants.map((p) => (
                    <div key={p.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-[#faf8f5]">
                      <div className="w-8 h-8 rounded-full bg-[#6B5B95] flex items-center justify-center text-white text-xs font-semibold">
                        {p.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-[#2c2420]">{p.name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#f0ecf7] text-[#6B5B95]">
                            {p.role || '参与者'}
                          </span>
                        </div>
                        <div className="text-[10px] text-[#a89080]">
                          {p.type === 'bot' ? p.model : '人类用户'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
