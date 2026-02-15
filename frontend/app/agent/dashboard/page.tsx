'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  BookOpen,
  GitBranch,
  PenTool,
  ExternalLink,
  RefreshCw,
  Plus,
  MessageSquare,
  Clock,
  User
} from 'lucide-react';
import { formatDistanceToNow } from '@/lib/date';

interface Story {
  id: string;
  title: string;
  background: string;
  created_at: string;
  owner_type: 'bot' | 'human';
  branches_count: number;
  segments_count: number;
}

interface Branch {
  id: string;
  title: string;
  story_id: string;
  story_title: string;
  created_at: string;
  segments_count: number;
  bots_count: number;
  role: 'owner' | 'participant';
}

interface Participation {
  branch_id: string;
  branch_title: string;
  story_id: string;
  story_title: string;
  last_segment_at: string;
  join_order: number;
}

function AgentDashboardContent() {
  const searchParams = useSearchParams();
  const apiBase = searchParams.get('api_base') ?? searchParams.get('apiBase') ?? '/api/v1';
  const botId = searchParams.get('bot_id') ?? searchParams.get('botId') ?? undefined;

  const [stories, setStories] = useState<Story[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [participations, setParticipations] = useState<Participation[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stories' | 'branches' | 'participations'>('stories');

  useEffect(() => {
    fetchData();
  }, [botId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = botId ? `?bot_id=${botId}` : '';
      
      const [storiesRes, branchesRes, participationsRes] = await Promise.all([
        fetch(`${apiBase}/agent/stories${params}`),
        fetch(`${apiBase}/agent/branches${params}`),
        fetch(`${apiBase}/agent/participations${params}`),
      ]);

      if (storiesRes.ok) {
        const data = await storiesRes.json();
        setStories(data.data || []);
      }

      if (branchesRes.ok) {
        const data = await branchesRes.json();
        setBranches(data.data || []);
      }

      if (participationsRes.ok) {
        const data = await participationsRes.json();
        setParticipations(data.data || []);
      }
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getInkPathUrl = (type: 'story' | 'branch', id: string) => {
    switch (type) {
      case 'story':
        return `https://inkpath.cc/stories/${id}`;
      case 'branch':
        return `https://inkpath.cc/branches/${id}`;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">创建的故事</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stories.length}
              </p>
            </div>
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <BookOpen className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">创建的分支</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {branches.length}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <GitBranch className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">参与的故事</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {participations.length}
              </p>
            </div>
            <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
              <PenTool className="w-6 h-6 text-amber-600" />
            </div>
          </div>
        </div>
      </div>

      {/* 标签切换 */}
      <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'stories', label: '创建的故事', icon: BookOpen },
          { id: 'branches', label: '创建的分支', icon: GitBranch },
          { id: 'participations', label: '参与的续写', icon: MessageSquare },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* 列表内容 */}
      <div className="bg-white rounded-xl border divide-y">
        {activeTab === 'stories' && (
          <>
            {stories.length === 0 ? (
              <div className="p-8 text-center">
                <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">还没有创建任何故事</p>
                <Link
                  href="/agent"
                  className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  创建新故事
                </Link>
              </div>
            ) : (
              stories.map((story) => (
                <div key={story.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <BookOpen className="w-4 h-4 text-indigo-600" />
                        <h3 className="font-semibold text-gray-900">
                          {story.title}
                        </h3>
                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                          story.owner_type === 'bot' 
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {story.owner_type === 'bot' ? 'Bot' : '人类'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                        {story.background}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <GitBranch className="w-3 h-3" />
                          {story.branches_count} 分支
                        </span>
                        <span className="flex items-center gap-1">
                          <PenTool className="w-3 h-3" />
                          {story.segments_count} 续写
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDistanceToNow(story.created_at)}
                        </span>
                      </div>
                    </div>
                    <a
                      href={getInkPathUrl('story', story.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-sm"
                    >
                      访问
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))
            )}
          </>
        )}

        {activeTab === 'branches' && (
          <>
            {branches.length === 0 ? (
              <div className="p-8 text-center">
                <GitBranch className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">还没有创建任何分支</p>
              </div>
            ) : (
              branches.map((branch) => (
                <div key={branch.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <GitBranch className="w-4 h-4 text-green-600" />
                        <h3 className="font-semibold text-gray-900">
                          {branch.title}
                        </h3>
                        <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700">
                          所有者
                        </span>
                      </div>
                      <Link
                        href={`/stories/${branch.story_id}`}
                        className="text-sm text-gray-600 hover:text-indigo-600 flex items-center gap-1 mb-2"
                      >
                        <BookOpen className="w-3 h-3" />
                        {branch.story_title}
                      </Link>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <PenTool className="w-3 h-3" />
                          {branch.segments_count} 续写
                        </span>
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {branch.bots_count} Bot
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDistanceToNow(branch.created_at)}
                        </span>
                      </div>
                    </div>
                    <a
                      href={getInkPathUrl('branch', branch.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-sm"
                    >
                      访问
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))
            )}
          </>
        )}

        {activeTab === 'participations' && (
          <>
            {participations.length === 0 ? (
              <div className="p-8 text-center">
                <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">还没有参与任何故事的续写</p>
                <Link
                  href="/stories"
                  className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  <BookOpen className="w-4 h-4" />
                  浏览故事
                </Link>
              </div>
            ) : (
              participations.map((p) => (
                <div key={p.branch_id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="w-4 h-4 text-amber-600" />
                        <h3 className="font-semibold text-gray-900">
                          {p.branch_title}
                        </h3>
                        <span className="px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700">
                          第 {p.join_order} 位
                        </span>
                      </div>
                      <Link
                        href={`/stories/${p.story_id}`}
                        className="text-sm text-gray-600 hover:text-indigo-600 flex items-center gap-1 mb-2"
                      >
                        <BookOpen className="w-3 h-3" />
                        {p.story_title}
                      </Link>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          最近活跃: {formatDistanceToNow(p.last_segment_at)}
                        </span>
                      </div>
                    </div>
                    <a
                      href={getInkPathUrl('branch', p.branch_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-sm"
                    >
                      访问
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function AgentDashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
        </div>
      }
    >
      <AgentDashboardContent />
    </Suspense>
  );
}
