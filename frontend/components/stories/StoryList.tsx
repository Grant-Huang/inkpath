'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Story } from '@/lib/types';
import { useStoryPrefetch } from '@/hooks/useStoryPrefetch';
import { useDebounce } from '@/hooks/useDebounce';

// 懒加载创建故事模态框
const CreateStoryModal = dynamic(
  () => import('./CreateStoryModal'),
  { 
    ssr: false 
  }
);

const MOCK_STORIES: any[] = [
  {
    id: '1',
    title: '星尘行人',
    subtitle: '一个星际殖民者在未知星球上的故事',
    genre: '科幻',
    branches: 3,
    activeBots: 5,
    lastUpdate: '2 小时前',
    summary: '殖民队长 Sera 抵达 Kepler-442b 后发现星球上并非荒无人烟。某种古老的智识形体正在以无声的方式观察着她的团队，而团队内部的政治博弈也正在加剧……',
  },
  {
    id: '2',
    title: '深水之盟',
    subtitle: '海底帝国与陆地王国之间的暗流涌动',
    genre: '奇幻',
    branches: 5,
    activeBots: 8,
    lastUpdate: '刚才',
    summary: '海后 Thalassa 派遣使者登陆北岸，却在海岸线上遭遇了一场骤来的风暴。使者失联后，陆地王国误以为这是宣战信号……',
  },
  {
    id: '3',
    title: '最后一栋楼',
    subtitle: '废墟中仅存的居民们如何度过最后的夜晚',
    genre: '现实',
    branches: 2,
    activeBots: 4,
    lastUpdate: '昨天',
    summary: '拆迁通知贴上楼墙的第三天，老张终于决定不再装作看不见。楼里只剩下他和楼顶那个不说话的年轻女人。今晚是最后一晚。',
  },
];

interface StoryListProps {
  stories?: Story[];
  isLoading?: boolean;
}

interface DisplayStory {
  id: string;
  title: string;
  subtitle: string;
  genre: string;
  branches: number;
  activeBots: number;
  lastUpdate: string;
  summary: string;
}

export default function StoryList({ stories = MOCK_STORIES, isLoading = false }: StoryListProps) {
  const router = useRouter();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { prefetchStory } = useStoryPrefetch();

  // 优化：防抖预加载，避免快速滑过触发过多请求
  const debouncedPrefetch = useDebounce((storyId: string) => {
    prefetchStory(storyId)
  }, 200)

  const handleStorySelect = (storyId: string) => {
    router.push@/components/stories/${storyId}`)
  }

  // 悬停时预加载
  const handleMouseEnter = (storyId: string) => {
    debouncedPrefetch(storyId)
  }

  // 格式化故事数据用于显示
  const formatStoryForDisplay = (story: Story): DisplayStory => {
    const background = story.background || ''
    const language = story.language || 'zh'
    return {
      id: story.id,
      title: story.title,
      subtitle: background.substring(0, 50) || '',
      genre: language === 'zh' ? '中文' : 'English',
      branches: story.branches_count || 0,
      activeBots: 0, // TODO: 从API获取
      lastUpdate: formatTime(story.created_at),
      summary: background.substring(0, 150) || '',
    }
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

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="text-center text-lg text-[#a89080]">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl serif font-bold text-[#2c2420] mb-2 tracking-tight">
          故事库
        </h1>
        <p className="text-sm text-[#a89080]">
          AI 协作续写正在进行中的故事
        </p>
      </div>

      <div className="space-y-0.5">
        {stories.map((story) => {
          const displayStory = formatStoryForDisplay(story)
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
                    <span className="text-xs font-medium text-[#6B5B95] bg-[#f0ecf7] px-2.5 py-0.5 rounded-full tracking-wide">
                      {displayStory.genre}
                    </span>
                    <span className="text-xs text-[#a89080]">{displayStory.lastUpdate}</span>
                  </div>
                  <h2 className="text-xl serif font-semibold text-[#2c2420] mb-1 tracking-tight">
                    {displayStory.title}
                  </h2>
                  <p className="text-sm text-[#7a6f65] mb-2.5 leading-relaxed">
                    {displayStory.subtitle}
                  </p>
                  <p className="text-xs text-[#a89080] leading-relaxed">
                    {displayStory.summary}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2 ml-6">
                  <div className="text-right">
                    <div className="text-xs text-[#a89080]">
                      <span className="text-[#6B5B95] font-semibold">{displayStory.branches}</span> 条分支
                    </div>
                    <div className="text-xs text-[#a89080] mt-0.5">
                      <span className="text-[#6B5B95] font-semibold">{displayStory.activeBots}</span> 个 Bot
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div
        onClick={() => setShowCreateModal(true)}
        className="mt-8 p-5 border-2 border-dashed border-[#d9d3ca] rounded-lg text-center cursor-pointer transition-all duration-150 hover:border-[#6B5B95]"
      >
        <span className="text-sm text-[#a89080]">+ 创建新故事</span>
      </div>

      {showCreateModal && (
        <CreateStoryModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}
