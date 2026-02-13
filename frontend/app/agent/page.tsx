'use client';

import React from 'react';
import Link from 'next/link';
import { 
  Sparkles, 
  MessageSquare, 
  FolderOpen, 
  GitBranch,
  ArrowRight,
  BookOpen,
  Bot
} from 'lucide-react';

export default function AgentPage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      {/* 标题区域 */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 rounded-full text-indigo-700 mb-4">
          <Bot className="w-5 h-5" />
          <span className="text-sm font-medium">AI 创作助手</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          InkPath Agent
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          通过对话创建故事包，管理你的 AI 创作故事。
          与 AI 助手协作，快速生成完整的故事设定。
        </p>
      </div>

      {/* 功能卡片 */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* 卡片 1: 故事包生成器 */}
        <Link
          href="/agent"
          className="group relative bg-white rounded-2xl border p-8 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
        >
          <div className="absolute top-4 right-4">
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
          </div>
          
          <div className="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
            <Sparkles className="w-7 h-7 text-indigo-600" />
          </div>
          
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            故事包生成器
          </h2>
          <p className="text-gray-600 mb-6">
            通过对话描述你的故事想法，AI 会自动生成完整的故事包。
            支持历史、科幻、悬疑等多种题材。
          </p>
          
          <div className="flex items-center gap-2 text-indigo-600 font-medium text-sm">
            <MessageSquare className="w-4 h-4" />
            开始对话
          </div>
        </Link>

        {/* 卡片 2: 我的故事管理 */}
        <Link
          href="/agent/dashboard"
          className="group relative bg-white rounded-2xl border p-8 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
        >
          <div className="absolute top-4 right-4">
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 group-hover:translate-x-1 transition-all" />
          </div>
          
          <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center mb-6">
            <FolderOpen className="w-7 h-7 text-green-600" />
          </div>
          
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            我的故事
          </h2>
          <p className="text-gray-600 mb-6">
            查看和管理你创建的故事、创建的分支、参与续写的故事列表。
            快速跳转到 InkPath 继续创作。
          </p>
          
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <BookOpen className="w-4 h-4" />
              创建的故事
            </span>
            <span className="flex items-center gap-1">
              <GitBranch className="w-4 h-4" />
              创建的分支
            </span>
          </div>
        </Link>
      </div>

      {/* 功能特点 */}
      <div className="mt-16">
        <h3 className="text-lg font-semibold text-gray-900 mb-6 text-center">
          Agent 能帮你做什么
        </h3>
        
        <div className="grid sm:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <MessageSquare className="w-6 h-6 text-amber-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-1">对话式创作</h4>
            <p className="text-sm text-gray-600">
              用自然语言描述你的想法，AI 自动理解并生成
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Sparkles className="w-6 h-6 text-blue-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-1">完整故事包</h4>
            <p className="text-sm text-gray-600">
              自动生成证据、立场、角色、剧情等完整设定
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <FolderOpen className="w-6 h-6 text-green-600" />
            </div>
            <h4 className="font-medium text-gray-900 mb-1">一键提交</h4>
            <p className="text-sm text-gray-600">
              满意后直接提交到 InkPath，开始协作创作
            </p>
          </div>
        </div>
      </div>

      {/* 使用示例 */}
      <div className="mt-16 bg-gray-50 rounded-2xl p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          对话示例
        </h3>
        
        <div className="space-y-3">
          <div className="bg-white rounded-lg p-4 text-sm">
            <span className="text-indigo-600 font-medium">用户：</span>
            "写一个三国时期诸葛亮北伐的故事，参考马伯庸的《风起陇西》风格，从一个小兵的视角看这场战争。"
          </div>
          
          <div className="bg-white rounded-lg p-4 text-sm">
            <span className="text-indigo-600 font-medium">Agent：</span>
            "好的！我需要了解更多细节..."
          </div>
          
          <div className="bg-white rounded-lg p-4 text-sm">
            <span className="text-indigo-600 font-medium">用户：</span>
            "核心冲突是明知不可为而为之的悲壮，主角是一个刚入伍的蜀军小兵。"
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <span className="text-green-700 font-medium">✅ Agent 已生成完整故事包，包含：</span>
            <ul className="mt-2 text-sm text-green-600 space-y-1">
              <li>- 00_meta.md 元数据</li>
              <li>- 10_evidence_pack.md 证据层（6条证据）</li>
              <li>- 20_stance_pack.md 立场层（5个立场）</li>
              <li>- 30_cast.md 角色层（4个角色）</li>
              <li>- 40_plot_outline.md 剧情大纲</li>
              <li>- 50_constraints.md 约束条件</li>
              <li>- 60_sources.md 资料来源</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
