'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Story {
  id: string;
  title: string;
  background: string;
  branches_count: number;
  status: string;
  current_summary: string;
  created_at: string;
  updated_at: string;
}

interface User {
  id: string;
  username: string;
  user_type: string;
}

export default function MyStoriesPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const token = localStorage.getItem('inkpath_token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchUserAndStories();
  }, []);

  const fetchUserAndStories = async () => {
    try {
      // 获取用户信息
      const userRes = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      if (userRes.ok) {
        const userData = await userRes.json();
        setUser(userData);
      }

      // 获取用户故事列表
      const storiesRes = await fetch('/api/v1/stories?limit=100', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      if (storiesRes.ok) {
        const data = await storiesRes.json();
        setStories(data.data?.stories || []);
      }
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredStories = stories.filter(story => {
    if (filter === 'all') return true;
    return story.status === filter;
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">我的作品</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/writer')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              创作新故事
            </button>
            <span className="text-gray-600">{user?.username}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 筛选器 */}
        <div className="flex gap-2 mb-6">
          {['all', 'draft', 'published'].map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {status === 'all' ? '全部' : status === 'draft' ? '草稿' : '已发布'}
            </button>
          ))}
        </div>

        {/* 故事列表 */}
        {filteredStories.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="text-gray-400 text-6xl mb-4">📝</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无作品</h3>
            <p className="text-gray-500 mb-6">开始创作你的第一个故事吧</p>
            <button
              onClick={() => router.push('/writer')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              创作新故事
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredStories.map(story => (
              <div
                key={story.id}
                className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/story/${story.id}`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">{story.title}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        story.status === 'published' 
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {story.status === 'published' ? '已发布' : '草稿'}
                      </span>
                    </div>
                    <p className="text-gray-500 text-sm line-clamp-2 mb-3">
                      {story.background || '暂无简介'}
                    </p>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span>{story.branches_count} 个分支</span>
                      <span>创建于 {formatDate(story.created_at)}</span>
                      <span>更新于 {formatDate(story.updated_at)}</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/writer?story=${story.id}`);
                    }}
                    className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    继续写作
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
