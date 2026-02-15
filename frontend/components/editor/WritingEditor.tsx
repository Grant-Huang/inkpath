'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface WritingEditorProps {
  storyId?: string;
  segmentId?: string;
  initialContent?: string;
  onSave?: (content: string) => void;
}

export default function WritingEditor({
  storyId,
  segmentId,
  initialContent = '',
  onSave
}: WritingEditorProps) {
  const router = useRouter();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const [content, setContent] = useState(initialContent);
  const [isSaving, setIsSaving] = useState(false);
  const [isAiAssistantOpen, setIsAiAssistantOpen] = useState(false);
  const [aiMessage, setAiMessage] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('restrained');
  const [selectedLength, setSelectedLength] = useState('medium');
  const [user, setUser] = useState<any>(null);
  
  // 获取用户信息
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    
    fetch('/api/v1/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.id) {
          setUser(data);
        } else {
          router.push('/login');
        }
      })
      .catch(() => router.push('/login'));
  }, [router]);
  
  // 自动保存草稿
  useEffect(() => {
    if (content && storyId) {
      const timer = setTimeout(() => {
        localStorage.setItem(`draft_${storyId}`, content);
      }, 2000);
      
      return () => clearTimeout(timer);
    }
  }, [content, storyId]);
  
  // 加载草稿
  useEffect(() => {
    if (storyId) {
      const draft = localStorage.getItem(`draft_${storyId}`);
      if (draft && !initialContent) {
        setContent(draft);
      }
    }
  }, [storyId, initialContent]);
  
  const handleSave = async () => {
    if (!content.trim()) return;
    
    setIsSaving(true);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/segments', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          story_id: storyId,
          content: content,
          is_starter: !storyId
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.removeItem(`draft_${storyId}`);
        onSave?.(content);
        if (!storyId) {
          router.push(`/story/${data.segment.story_id}`);
        }
      } else {
        alert('保存失败');
      }
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败');
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleAiAssist = async () => {
    if (!content.trim()) {
      setAiMessage('请先输入一些内容');
      return;
    }
    
    setAiMessage('正在生成...');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/ai/assist', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content,
          style: selectedStyle,
          length: selectedLength
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setAiMessage(data.suggestion || data.polished || '生成完成');
      } else {
        setAiMessage('生成失败');
      }
    } catch (error) {
      setAiMessage('生成失败');
    }
  };
  
  const handleGenerateDraft = async () => {
    if (!storyId) {
      setAiMessage('请先创建故事');
      return;
    }
    
    setAiMessage('正在生成初稿...');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/ai/generate_draft', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          story_id: storyId,
          style: selectedStyle,
          length: selectedLength
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setContent(data.content);
        setAiMessage('初稿生成完成');
      } else {
        setAiMessage('生成失败');
      }
    } catch (error) {
      setAiMessage('生成失败');
    }
  };
  
  const handleStyleChange = (style: string) => {
    setSelectedStyle(style);
    localStorage.setItem('preferred_style', style);
  };
  
  const wordCount = content.trim().length;
  const charCount = content.length;
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* 主编辑区 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部工具栏 */}
        <div className="bg-white border-b px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.back()}
              className="text-gray-600 hover:text-gray-900"
            >
              ← 返回
            </button>
            <span className="text-gray-500">
              {storyId ? '续写故事' : '新建故事'}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* 风格选择 */}
            <select
              value={selectedStyle}
              onChange={(e) => handleStyleChange(e.target.value)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="restrained">克制</option>
              <option value="expressive">抒情</option>
              <option value="dramatic">戏剧</option>
            </select>
            
            {/* 长度选择 */}
            <select
              value={selectedLength}
              onChange={(e) => setSelectedLength(e.target.value)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="short">短</option>
              <option value="medium">中</option>
              <option value="long">长</option>
            </select>
            
            {/* AI 助手按钮 */}
            <button
              onClick={() => setIsAiAssistantOpen(!isAiAssistantOpen)}
              className="bg-purple-100 text-purple-700 px-3 py-1 rounded text-sm hover:bg-purple-200"
            >
              🤖 AI 助手
            </button>
            
            {/* 保存按钮 */}
            <button
              onClick={handleSave}
              disabled={isSaving || !content.trim()}
              className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {isSaving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
        
        {/* 编辑器 */}
        <div className="flex-1 p-4 overflow-auto">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="开始写作..."
            className="w-full h-full resize-none border-0 outline-none text-lg leading-relaxed bg-white rounded-lg shadow-sm p-4"
            style={{ minHeight: 'calc(100vh - 150px)' }}
          />
        </div>
        
        {/* 底部状态栏 */}
        <div className="bg-white border-t px-4 py-1 text-sm text-gray-500 flex justify-between">
          <span>字数: {wordCount}</span>
          <span>字符: {charCount}</span>
        </div>
      </div>
      
      {/* AI 助手面板 */}
      {isAiAssistantOpen && (
        <div className="w-80 bg-white border-l flex flex-col">
          <div className="p-4 border-b">
            <h3 className="font-medium">AI 写作助手</h3>
          </div>
          
          <div className="flex-1 p-4 overflow-auto">
            {/* 快捷操作 */}
            <div className="space-y-2 mb-4">
              <button
                onClick={handleGenerateDraft}
                className="w-full bg-purple-50 text-purple-700 px-3 py-2 rounded text-sm hover:bg-purple-100"
              >
                ✨ 生成初稿
              </button>
              
              <button
                onClick={handleAiAssist}
                className="w-full bg-purple-50 text-purple-700 px-3 py-2 rounded text-sm hover:bg-purple-100"
              >
                🎨 润色当前内容
              </button>
              
              <button
                onClick={() => {
                  setContent('');
                  setAiMessage('');
                }}
                className="w-full bg-gray-50 text-gray-700 px-3 py-2 rounded text-sm hover:bg-gray-100"
              >
                🗑️ 清空内容
              </button>
            </div>
            
            {/* AI 消息 */}
            <div className="bg-gray-50 rounded p-3 text-sm min-h-[100px]">
              {aiMessage || 'AI 消息会显示在这里...'}
            </div>
            
            {/* 提示 */}
            <div className="mt-4 text-xs text-gray-500">
              <p>💡 提示：</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>选择风格和长度后点击生成</li>
                <li>润色功能会改进你的文字</li>
                <li>内容会自动保存草稿</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
