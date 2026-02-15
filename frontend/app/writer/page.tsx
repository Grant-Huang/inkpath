'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  username: string;
  email: string;
  user_type: string;
}

interface Story {
  id: string;
  title: string;
  background: string;
  style_rules: string;
  language: string;
}

export default function WriterPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [story, setStory] = useState<Story | null>(null);
  const [content, setContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [aiMessage, setAiMessage] = useState('');
  const [aiChatHistory, setAiChatHistory] = useState<Array<{role: string; content: string}>>([]);

  useEffect(() => {
    // 检查登录状态
    const token = localStorage.getItem('inkpath_token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
    }
  };

  const generateContent = async (prompt: string) => {
    setIsGenerating(true);
    try {
      const response = await fetch('/api/v1/ai/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({
          prompt,
          style: story?.style_rules || '克制,冷峻,悬念',
          language: story?.language || 'zh'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setContent(data.content);
      }
    } catch (error) {
      console.error('生成失败:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const polishContent = async () => {
    if (!content) return;
    setIsGenerating(true);
    try {
      const response = await fetch('/api/v1/ai/polish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({ content })
      });
      
      if (response.ok) {
        const data = await response.json();
        setContent(data.content);
      }
    } catch (error) {
      console.error('润色失败:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const publishSegment = async () => {
    if (!content || !story) return;
    setIsPublishing(true);
    
    try {
      const response = await fetch(`/api/v1/branches/${story.id}/segments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({ content, is_starter: false })
      });
      
      if (response.ok) {
        alert('发布成功！');
        router.push(`/story/${story.id}`);
      }
    } catch (error) {
      console.error('发布失败:', error);
    } finally {
      setIsPublishing(false);
    }
  };

  const sendAiMessage = async () => {
    if (!aiMessage.trim()) return;
    
    const newHistory = [...aiChatHistory, { role: 'user', content: aiMessage }];
    setAiChatHistory(newHistory);
    setAiMessage('');
    
    try {
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({
          message: aiMessage,
          context: story?.background,
          style_rules: story?.style_rules
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setAiChatHistory([...newHistory, { role: 'assistant', content: data.reply }]);
      }
    } catch (error) {
      console.error('AI对话失败:', error);
    }
  };

  if (!user) {
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
          <h1 className="text-xl font-bold text-gray-900">InkPath - 写作助手</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">{user.username}</span>
            <button
              onClick={() => {
                localStorage.removeItem('inkpath_token');
                router.push('/');
              }}
              className="text-sm text-red-600 hover:text-red-800"
            >
              退出
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 写作区 */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">写作区域</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={polishContent}
                    disabled={isGenerating || !content}
                    className="px-4 py-2 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 disabled:opacity-50"
                  >
                    {isGenerating ? '润色中...' : 'AI 润色'}
                  </button>
                  <button
                    onClick={publishSegment}
                    disabled={isPublishing || !content}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isPublishing ? '发布中...' : '发布'}
                  </button>
                </div>
              </div>
              
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="在这里开始写作..."
                className="w-full h-96 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              
              <div className="mt-2 text-sm text-gray-500 text-right">
                {content.length} 字
              </div>
            </div>

            {/* 快捷操作 */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">快捷生成</h3>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => generateContent('继续当前情节')}
                  disabled={isGenerating}
                  className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                >
                  续写
                </button>
                <button
                  onClick={() => generateContent('增加一个悬念')}
                  disabled={isGenerating}
                  className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                >
                  加悬念
                </button>
                <button
                  onClick={() => generateContent('增加一段对话')}
                  disabled={isGenerating}
                  className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                >
                  加对话
                </button>
                <button
                  onClick={() => generateContent('描写环境')}
                  disabled={isGenerating}
                  className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                >
                  写环境
                </button>
              </div>
            </div>
          </div>

          {/* 侧边栏 */}
          <div className="space-y-4">
            {/* AI 对话 */}
            <div className="bg-white rounded-lg shadow-sm">
              <div 
                className="p-4 border-b cursor-pointer flex items-center justify-between"
                onClick={() => setShowAIChat(!showAIChat)}
              >
                <h3 className="font-medium text-gray-900">AI 写作助手</h3>
                <span className="text-gray-500">{showAIChat ? '收起' : '展开'}</span>
              </div>
              
              {showAIChat && (
                <div className="p-4">
                  <div className="h-64 overflow-y-auto border rounded-lg p-3 space-y-3 mb-3">
                    {aiChatHistory.length === 0 ? (
                      <div className="text-sm text-gray-500 text-center">
                        向 AI 助手提问，获得写作建议
                      </div>
                    ) : (
                      aiChatHistory.map((msg, i) => (
                        <div key={i} className={`text-sm ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                          <span className={`inline-block px-3 py-2 rounded-lg ${msg.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                            {msg.content}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={aiMessage}
                      onChange={(e) => setAiMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendAiMessage()}
                      placeholder="输入你的问题..."
                      className="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={sendAiMessage}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                    >
                      发送
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* 写作指南 */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="font-medium text-gray-900 mb-3">写作指南</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• 保持克制、冷峻的风格</p>
                <p>• 短句为主，动作+对话</p>
                <p>• 注意故事连贯性</p>
                <p>• 每个片段 400-500 字</p>
              </div>
            </div>

            {/* 风格规则 */}
            {story && (
              <div className="bg-white rounded-lg shadow-sm p-4">
                <h3 className="font-medium text-gray-900 mb-3">风格规则</h3>
                <div className="flex flex-wrap gap-1">
                  {story.style_rules.split(',').map((rule, i) => (
                    <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                      {rule}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
