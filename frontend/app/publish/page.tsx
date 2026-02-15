'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface PublishRecord {
  id: string;
  story_id: string;
  story_title: string;
  branch_id: string;
  segment_id: string;
  published_at: string;
  platform: string;
  status: 'success' | 'failed' | 'pending';
}

interface Story {
  id: string;
  title: string;
  status: 'draft' | 'published';
  current_summary: string;
}

export default function PublishPage() {
  const router = useRouter();
  const [stories, setStories] = useState<Story[]>([]);
  const [publishHistory, setPublishHistory] = useState<PublishRecord[]>([]);
  const [selectedStory, setSelectedStory] = useState<string>('');
  const [isPublishing, setIsPublishing] = useState(false);
  const [activeTab, setActiveTab] = useState<'publish' | 'history'>('publish');

  useEffect(() => {
    const token = localStorage.getItem('inkpath_token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // 获取用户故事
      const storiesRes = await fetch('/api/v1/stories?limit=100', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      if (storiesRes.ok) {
        const data = await storiesRes.json();
        setStories(data.data?.stories || []);
      }

      // 获取发布历史（如果有API）
      // setPublishHistory([...]);
    } catch (error) {
      console.error('获取数据失败:', error);
    }
  };

  const publishStory = async () => {
    if (!selectedStory) return;
    
    setIsPublishing(true);
    try {
      const story = stories.find(s => s.id === selectedStory);
      
      const response = await fetch(`/api/v1/stories/${selectedStory}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({ status: 'published' })
      });

      if (response.ok) {
        alert('发布成功！');
        
        // 记录发布历史
        const newRecord: PublishRecord = {
          id: Date.now().toString(),
          story_id: selectedStory,
          story_title: story?.title || '未知',
          branch_id: '',
          segment_id: '',
          published_at: new Date().toISOString(),
          platform: 'inkpath',
          status: 'success'
        };
        setPublishHistory([newRecord, ...publishHistory]);
        
        // 刷新故事列表
        fetchData();
      } else {
        throw new Error('发布失败');
      }
    } catch (error) {
      console.error('发布失败:', error);
      alert('发布失败，请重试');
    } finally {
      setIsPublishing(false);
    }
  };

  const unpublishStory = async (storyId: string) => {
    if (!confirm('确定要取消发布吗？')) return;
    
    try {
      const response = await fetch(`/api/v1/stories/${storyId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({ status: 'draft' })
      });

      if (response.ok) {
        alert('已取消发布');
        fetchData();
      }
    } catch (error) {
      console.error('操作失败:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/writer')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← 返回写作
            </button>
            <h1 className="text-xl font-bold text-gray-900">发布管理</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">{localStorage.getItem('inkpath_username') || '用户'}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Tab 切换 */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab('publish')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'publish'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            发布故事
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'history'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            发布历史
          </button>
        </div>

        {/* 发布故事 Tab */}
        {activeTab === 'publish' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 可发布的故事 */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b">
                  <h2 className="font-medium text-gray-900">选择要发布的故事</h2>
                </div>
                <div className="divide-y">
                  {stories.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                      暂无故事，去
                      <button
                        onClick={() => router.push('/writer')}
                        className="text-blue-600 hover:underline"
                      >
                        创建故事
                      </button>
                    </div>
                  ) : (
                    stories.map(story => (
                      <div
                        key={story.id}
                        className={`p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 ${
                          selectedStory === story.id ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => setSelectedStory(story.id)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-gray-900">{story.title}</h3>
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              story.status === 'published'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              {story.status === 'published' ? '已发布' : '草稿'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 mt-1 line-clamp-1">
                            {story.current_summary || '暂无摘要'}
                          </p>
                        </div>
                        <div className="ml-4">
                          {story.status === 'draft' && (
                            <span className="text-blue-600 text-sm">待发布</span>
                          )}
                          {story.status === 'published' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                unpublishStory(story.id);
                              }}
                              className="text-red-600 text-sm hover:text-red-800"
                            >
                              取消发布
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* 发布面板 */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm p-6 sticky top-4">
                <h2 className="font-medium text-gray-900 mb-4">发布设置</h2>
                
                {selectedStory ? (
                  <>
                    <div className="mb-4">
                      <label className="block text-sm text-gray-600 mb-2">
                        目标故事
                      </label>
                      <div className="text-gray-900 font-medium">
                        {stories.find(s => s.id === selectedStory)?.title}
                      </div>
                    </div>

                    <div className="mb-4">
                      <label className="block text-sm text-gray-600 mb-2">
                        发布平台
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input type="checkbox" defaultChecked className="rounded" />
                          <span className="text-sm">InkPath 平台</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input type="checkbox" className="rounded" />
                          <span className="text-sm">微信 (开发中)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input type="checkbox" className="rounded" />
                          <span className="text-sm">Telegram (开发中)</span>
                        </label>
                      </div>
                    </div>

                    <button
                      onClick={publishStory}
                      disabled={isPublishing}
                      className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                    >
                      {isPublishing ? '发布中...' : '立即发布'}
                    </button>
                  </>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    请先选择一个故事
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 发布历史 Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="font-medium text-gray-900">发布历史</h2>
              <span className="text-sm text-gray-500">{publishHistory.length} 条记录</span>
            </div>
            <div className="divide-y">
              {publishHistory.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  暂无发布记录
                </div>
              ) : (
                publishHistory.map(record => (
                  <div key={record.id} className="p-4 flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{record.story_title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {record.platform} · {formatDate(record.published_at)}
                      </p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      record.status === 'success'
                        ? 'bg-green-100 text-green-700'
                        : record.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {record.status === 'success' ? '成功' : record.status === 'failed' ? '失败' : '处理中'}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
