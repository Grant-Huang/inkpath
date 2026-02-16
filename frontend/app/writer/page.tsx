'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Story {
  id: string;
  title: string;
  background: string;
}

export default function WriterPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [story, setStory] = useState<Story | null>(null);
  const [content, setContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  const apiGet = async (path: string) => {
    const token = localStorage.getItem('jwt_token');
    const res = await fetch(`/api/proxy${path}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  };

  const apiPost = async (path: string, data: any) => {
    const token = localStorage.getItem('jwt_token');
    const res = await fetch(`/api/proxy${path}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  };

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    try {
      const data = await apiGet('/users/me');
      setUser(data.data);
    } catch (err) {
      setError('获取用户信息失败');
    }
  };

  const generateContent = async () => {
    if (!content) return;
    setIsGenerating(true);
    setError('');
    try {
      // 简化的生成逻辑
      const data = await apiPost('/ai/generate', { 
        prompt: content,
        style: story?.background || '克制,冷峻',
        language: 'zh'
      });
      setContent(data.content || content);
    } catch (err: any) {
      setError(err.message || '生成失败');
    } finally {
      setIsGenerating(false);
    }
  };

  const publishStory = async () => {
    if (!content || !story) return;
    setIsGenerating(true);
    try {
      await apiPost(`/branches/${story.id}/segments`, { content });
      router.push(`/stories/${story.id}`);
    } catch (err: any) {
      setError(err.message || '发布失败');
    } finally {
      setIsGenerating(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">📝 故事续写</h1>
        {user && <p className="text-[#7a6f65] mb-6">用户: {user.name}</p>}
        
        <p className="text-sm text-[#7a6f65] mb-6">
          在这里你可以为喜爱的故事创作新片段。输入内容后点击「发布」提交到故事分支。
        </p>
        
        <div className="bg-white rounded-xl border border-[#ede9e3] p-6 mb-6">
          <h2 className="font-semibold mb-4">创作新片段</h2>
          <textarea
            className="w-full h-48 p-3 border border-[#ede9e3] rounded-lg text-sm mb-4"
            placeholder="输入你的故事内容..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="flex gap-4">
            <button
              onClick={generateContent}
              disabled={isGenerating}
              className="px-4 py-2 bg-[#6B5B95] text-white rounded-lg text-sm disabled:opacity-50"
            >
              {isGenerating ? '生成中...' : 'AI 续写'}
            </button>
            <button
              onClick={publishStory}
              disabled={isGenerating || !content}
              className="px-4 py-2 bg-[#2c2420] text-white rounded-lg text-sm disabled:opacity-50"
            >
              发布
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
