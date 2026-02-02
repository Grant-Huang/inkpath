'use client';

import { useState } from 'react';

interface SummaryCardProps {
  summary: string;
  coversUpTo: number;
  updatedAt: string;
}

export default function SummaryCard({
  summary,
  coversUpTo,
  updatedAt,
}: SummaryCardProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="bg-[#faf8f5] border border-[#ede9e3] rounded-lg overflow-hidden mb-7">
      <div
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between p-3.5 cursor-pointer select-none"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-sm">📌</span>
          <span className="text-sm font-semibold text-[#2c2420]">当前进展摘要</span>
          <span className="text-[10px] text-[#a89080] bg-[#ede9e3] px-2 py-0.5 rounded-full">
            覆盖到第 {coversUpTo} 段
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-[#a89080]">{updatedAt}</span>
          <span
            className={`text-xs text-[#a89080] transition-transform duration-200 ${
              expanded ? '' : 'rotate-180'
            }`}
          >
            ▼
          </span>
        </div>
      </div>
      {expanded && (
        <div className="px-5 pb-4.5 border-t border-[#ede9e3] pt-4">
          <p className="text-sm text-[#5a4f45] leading-relaxed mb-3">
            {summary}
          </p>
          <div className="flex gap-4 pt-2.5 border-t border-[#ede9e3]">
            <span className="text-xs text-[#a89080]">🤖 由 AI 自动生成</span>
            <span className="text-xs text-[#a89080]">⏱ 每 3 段刷新一次</span>
          </div>
        </div>
      )}
    </div>
  );
}
