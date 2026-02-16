'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function PublishPage() {
  const router = useRouter();
  const [stories, setStories] = useState<any[]>([]);
  const [selectedStory, setSelectedStory] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchStories();
  }, []);

  const fetchStories = async () => {
    try {
      const res = await fetch('/api/proxy/stories?limit=100');
      const data = await res.json();
      setStories(data.data?.stories || []);
    } catch (err) {
      console.error('获取故事失败:', err);
    }
  };

  const handlePublish = async () => {
    if (!selectedStory) return;
    router.push(`/stories/${selectedStory}`);
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">发布管理</h1>
        
        <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
          <h2 className="font-semibold mb-4">选择要查看的故事</h2>
          
          <select
            value={selectedStory}
            onChange={(e) => setSelectedStory(e.target.value)}
            className="w-full px-3 py-2 border border-[#ede9e3] rounded-lg mb-4"
          >
            <option value="">请选择故事</option>
            {stories.map((story) => (
              <option key={story.id} value={story.id}>{story.title}</option>
            ))}
          </select>

          <button
            onClick={handlePublish}
            disabled={!selectedStory}
            className="px-4 py-2 bg-[#6B5B95] text-white rounded-lg text-sm disabled:opacity-50"
          >
            查看并发布
          </button>
        </div>
      </div>
    </div>
  );
}
