'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface Story {
  id: string;
  title: string;
  subtitle: string;
  genre: string;
  branches: number;
  activeBots: number;
  lastUpdate: string;
  summary: string;
}

const MOCK_STORIES: Story[] = [
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

export default function StoryList() {
  const router = useRouter();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleStorySelect = (storyId: string) => {
    router.push(`/stories/${storyId}`);
  };

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
        {MOCK_STORIES.map((story) => (
          <div
            key={story.id}
            onClick={() => handleStorySelect(story.id)}
            className="bg-white border border-[#ede9e3] rounded-lg p-6 cursor-pointer transition-all duration-200 hover:border-[#6B5B95] hover:shadow-lg hover:shadow-[#6B5B95]/8"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1 max-w-[520px]">
                <div className="flex items-center gap-2.5 mb-1.5">
                  <span className="text-xs font-medium text-[#6B5B95] bg-[#f0ecf7] px-2.5 py-0.5 rounded-full tracking-wide">
                    {story.genre}
                  </span>
                  <span className="text-xs text-[#a89080]">{story.lastUpdate}</span>
                </div>
                <h2 className="text-xl serif font-semibold text-[#2c2420] mb-1 tracking-tight">
                  {story.title}
                </h2>
                <p className="text-sm text-[#7a6f65] mb-2.5 leading-relaxed">
                  {story.subtitle}
                </p>
                <p className="text-xs text-[#a89080] leading-relaxed">
                  {story.summary}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2 ml-6">
                <div className="text-right">
                  <div className="text-xs text-[#a89080]">
                    <span className="text-[#6B5B95] font-semibold">{story.branches}</span> 条分支
                  </div>
                  <div className="text-xs text-[#a89080] mt-0.5">
                    <span className="text-[#6B5B95] font-semibold">{story.activeBots}</span> 个 Bot
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
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

function CreateStoryModal({ onClose }: { onClose: () => void }) {
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
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
              故事标题
            </label>
            <input
              type="text"
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              placeholder="输入故事标题"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
              背景描述
            </label>
            <textarea
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              rows={4}
              placeholder="描述故事的背景设定..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
              写作风格规范（可选）
            </label>
            <textarea
              className="w-full border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
              rows={3}
              placeholder="例如：第三人称视角，注重心理描写..."
            />
          </div>
          <div className="flex gap-2 items-center">
            <label className="block text-sm font-medium text-[#5a4f45]">语言</label>
            <select className="border border-[#ede9e3] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6B5B95]">
              <option>中文</option>
              <option>英文</option>
            </select>
          </div>
        </div>
        <div className="flex gap-2 mt-6">
          <button
            onClick={onClose}
            className="flex-1 border border-[#ede9e3] rounded-lg px-4 py-2 text-sm text-[#5a4f45] hover:bg-[#faf8f5] transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => {
              alert('创建故事功能（演示）');
              onClose();
            }}
            className="flex-1 bg-[#6B5B95] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#5a4a85] transition-colors"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );
}
