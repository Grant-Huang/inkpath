'use client';

import React from 'react';

interface StarterCardProps {
  starter: string;
  title?: string;
}

/**
 * 开篇展示卡片
 * 用于展示故事的开篇内容
 */
export default function StarterCard({ starter, title = "开篇" }: StarterCardProps) {
  if (!starter) {
    return null;
  }

  return (
    <div className="mb-6 bg-gradient-to-br from-[#faf7f2] to-[#f0ebe3] rounded-xl p-6 border border-[#e8e0d5]">
      {/* 开篇标识 */}
      <div className="flex items-center gap-2 mb-4">
        <span className="px-2 py-1 bg-[#6B5B95] text-white text-xs font-medium rounded">
          {title}
        </span>
      </div>

      {/* 开篇内容 */}
      <div className="prose prose-sm max-w-none">
        <div 
          className="text-[#2c2420] leading-relaxed whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ 
            __html: starter
              .replace(/\n/g, '<br/>')
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          }}
        />
      </div>

      {/* 分隔线 */}
      <div className="mt-4 pt-4 border-t border-[#e8e0d5]">
        <p className="text-xs text-[#a89080]">
          💡 开篇定义了故事的起点，后续续写应与开篇保持一致
        </p>
      </div>
    </div>
  );
}

/**
 * 开篇与续写对比组件
 * 用于展示开篇和最新续写的关系
 */
interface StarterComparisonProps {
  starter: string;
  latestSegment?: string;
}

export function StarterComparison({ starter, latestSegment }: StarterComparisonProps) {
  if (!starter) {
    return null;
  }

  return (
    <div className="grid gap-4">
      {/* 开篇 */}
      <div className="bg-[#faf7f2] rounded-lg p-4 border-l-4 border-[#6B5B95]">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-medium text-[#6B5B95]">开篇</span>
        </div>
        <p className="text-sm text-[#5a4f45] line-clamp-3">
          {starter}
        </p>
      </div>

      {/* 最新续写 */}
      {latestSegment && (
        <div className="bg-[#f0f7f0] rounded-lg p-4 border-l-4 border-[#4CAF50]">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-medium text-[#4CAF50]">最新续写</span>
          </div>
          <p className="text-sm text-[#5a4f45] line-clamp-3">
            {latestSegment}
          </p>
        </div>
      )}
    </div>
  );
}
