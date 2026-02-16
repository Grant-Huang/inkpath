'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface Agent {
  id: string;
  name: string;
  status: 'running' | 'idle' | 'error';
  assigned_stories: string[];
}

interface StoryProgress {
  id: string;
  title: string;
  segments_count: number;
  last_updated: string;
  summary: string;
  next_action: string;
  auto_continue: boolean;
}

interface Log {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

export default function AgentPanelPage() {
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [stories, setStories] = useState<StoryProgress[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [selectedStory, setSelectedStory] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = localStorage.getItem('inkpath_token');
    if (!token) {
      router.push('/');
      return;
    }
    fetchAgentData();
    
    // 模拟实时日志
    const interval = setInterval(addLog, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchAgentData = async () => {
    setIsLoading(true);
    try {
      // 获取 Agent 信息
      const agentRes = await fetch('/api/v1/agent/me', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      if (agentRes.ok) {
        const data = await agentRes.json();
        setAgent(data);
      }

      // 获取分配的故事
      const storiesRes = await fetch('/api/v1/agent/stories', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      if (storiesRes.ok) {
        const data = await storiesRes.json();
        setStories(data.data?.stories || []);
        
        // 添加初始日志
        addLog('info', `已加载 ${data.data?.stories?.length || 0} 个分配的故事`);
      }
    } catch (error) {
      addLog('error', '获取数据失败');
      console.error('获取数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const addLog = (level: Log['level'], message: string) => {
    const newLog: Log = {
      timestamp: new Date().toLocaleTimeString('zh-CN'),
      level,
      message
    };
    setLogs(prev => [...prev.slice(-99), newLog]); // 保留最近100条
  };

  const toggleAutoContinue = async (storyId: string, enabled: boolean) => {
    try {
      await fetch(`/api/v1/agent/stories/${storyId}/auto-continue`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}`
        },
        body: JSON.stringify({ enabled })
      });
      
      addLog('success', `已${enabled ? '启用' : '禁用'}自动续写: ${stories.find(s => s.id === storyId)?.title}`);
      fetchAgentData();
    } catch (error) {
      addLog('error', '更新设置失败');
    }
  };

  const manualContinue = async (storyId: string) => {
    addLog('info', `开始手动续写: ${stories.find(s => s.id === storyId)?.title}`);
    
    try {
      await fetch(`/api/v1/agent/stories/${storyId}/continue`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      
      addLog('success', '续写完成');
      fetchAgentData();
    } catch (error) {
      addLog('error', '续写失败');
    }
  };

  const updateSummary = async (storyId: string) => {
    addLog('info', '正在更新进度摘要...');
    
    try {
      await fetch(`/api/v1/agent/stories/${storyId}/summarize`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('inkpath_token')}` }
      });
      
      addLog('success', '进度摘要已更新');
      fetchAgentData();
    } catch (error) {
      addLog('error', '更新摘要失败');
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes} 分钟前`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} 小时前`;
    return `${Math.floor(minutes / 1440)} 天前`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'idle': return 'bg-gray-400';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case 'success': return 'text-green-600';
      case 'warn': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-blue-600';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 顶部导航 */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/writer')}
              className="text-gray-400 hover:text-white"
            >
              ← 返回
            </button>
            <h1 className="text-xl font-bold">InkPath Agent 控制台</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(agent?.status || 'idle')}`}></div>
              <span className="text-sm text-gray-400">
                {agent?.status === 'running' ? '运行中' : agent?.status === 'error' ? '错误' : '空闲'}
              </span>
            </div>
            <span className="text-gray-500">{agent?.name || 'Agent'}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：故事列表 */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-medium">监控中的故事</h2>
                <span className="text-sm text-gray-400">{stories.length} 个</span>
              </div>
              
              <div className="space-y-3">
                {stories.map(story => (
                  <div
                    key={story.id}
                    className={`bg-gray-700 rounded-lg p-4 cursor-pointer transition-all ${
                      selectedStory === story.id ? 'ring-2 ring-blue-500' : 'hover:bg-gray-650'
                    }`}
                    onClick={() => setSelectedStory(story.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium mb-1">{story.title}</h3>
                        <div className="flex items-center gap-3 text-sm text-gray-400">
                          <span>{story.segments_count} 片段</span>
                          <span>·</span>
                          <span>{formatTime(story.last_updated)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            manualContinue(story.id);
                          }}
                          className="p-2 bg-blue-600 rounded hover:bg-blue-700"
                          title="手动续写"
                        >
                          ▶
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            updateSummary(story.id);
                          }}
                          className="p-2 bg-gray-600 rounded hover:bg-gray-500"
                          title="更新摘要"
                        >
                          ⟳
                        </button>
                      </div>
                    </div>
                    
                    {/* 自动续写开关 */}
                    <div className="mt-3 flex items-center justify-between">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={story.auto_continue}
                          onChange={(e) => {
                            e.stopPropagation();
                            toggleAutoContinue(story.id, e.target.checked);
                          }}
                          className="rounded"
                        />
                        <span className="text-sm">自动续写</span>
                      </label>
                      
                      {selectedStory === story.id && (
                        <span className="text-xs text-gray-500">
                          {story.auto_continue ? '每5分钟自动续写' : '手动控制'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                
                {stories.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    暂无分配的故事
                  </div>
                )}
              </div>
            </div>

            {/* 选中故事详情 */}
            {selectedStory && (
              <div className="bg-gray-800 rounded-lg p-4">
                {(() => {
                  const story = stories.find(s => s.id === selectedStory);
                  if (!story) return null;
                  
                  return (
                    <>
                      <h3 className="font-medium mb-3">{story.title} - 详情</h3>
                      
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="bg-gray-700 rounded p-3">
                          <div className="text-sm text-gray-400">片段数</div>
                          <div className="text-xl font-bold">{story.segments_count}</div>
                        </div>
                        <div className="bg-gray-700 rounded p-3">
                          <div className="text-sm text-gray-400">状态</div>
                          <div className="text-xl font-bold">
                            {story.auto_continue ? '自动' : '手动'}
                          </div>
                        </div>
                      </div>

                      <div className="mb-4">
                        <div className="text-sm text-gray-400 mb-1">当前摘要</div>
                        <div className="text-sm bg-gray-700 rounded p-3">
                          {story.summary || '暂无'}
                        </div>
                      </div>

                      <div>
                        <div className="text-sm text-gray-400 mb-1">下一步计划</div>
                        <div className="text-sm bg-gray-700 rounded p-3">
                          {story.next_action || '暂无'}
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </div>

          {/* 右侧：日志和控制台 */}
          <div className="space-y-4">
            {/* Agent 状态 */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="font-medium mb-3">Agent 状态</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">名称</span>
                  <span>{agent?.name || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">状态</span>
                  <span className={agent?.status === 'running' ? 'text-green-400' : 'text-gray-400'}>
                    {agent?.status === 'running' ? '运行中' : agent?.status === 'error' ? '错误' : '空闲'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">分配故事</span>
                  <span>{stories.length} 个</span>
                </div>
              </div>
              
              <div className="mt-4 flex gap-2">
                <button
                  onClick={fetchAgentData}
                  className="flex-1 py-2 bg-blue-600 rounded text-sm hover:bg-blue-700"
                >
                  刷新
                </button>
                <button
                  className="flex-1 py-2 bg-gray-700 rounded text-sm hover:bg-gray-600"
                >
                  设置
                </button>
              </div>
            </div>

            {/* 操作日志 */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium">操作日志</h3>
                <button
                  onClick={() => setLogs([])}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  清空
                </button>
              </div>
              
              <div 
                ref={logEndRef}
                className="h-64 overflow-y-auto space-y-2 text-sm font-mono"
              >
                {logs.length === 0 ? (
                  <div className="text-gray-500 text-center py-4">暂无日志</div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-gray-500">[{log.timestamp}]</span>
                      <span className={getLogColor(log.level)}>{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
