'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Story {
  id: string;
  title: string;
  background: string;
  status: string;
  created_at: string;
}

export default function MyStoriesPage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    fetchStories();
  }, []);

  const fetchStories = async () => {
    try {
      const res = await fetch('/api/proxy/stories?limit=100', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` },
      });
      const data = await res.json();
      setStories(data.data?.stories || []);
    } catch (err) {
      console.error('获取故事失败:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">加载中...</div>;
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">我的故事</h1>
          <Link href="/writer" className="px-4 py-2 bg-[#6B5B95] text-white rounded-lg text-sm">
            创建故事
          </Link>
        </div>
        
        {stories.length === 0 ? (
          <p className="text-[#7a6f65]">暂无故事，去 <Link href="/writer" className="text-[#6B5B95]">创建</Link> 一个吧</p>
        ) : (
          <div className="grid gap-4">
            {stories.map((story) => (
              <Link key={story.id} href={`/stories/${story.id}`} className="block bg-white rounded-xl border border-[#ede9e3] p-4 hover:border-[#6B5B95]">
                <h3 className="font-semibold">{story.title}</h3>
                <p className="text-sm text-[#7a6f65] mt-1 truncate">{story.background}</p>
                <p className="text-xs text-[#a89080] mt-2">{new Date(story.created_at).toLocaleDateString()}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
