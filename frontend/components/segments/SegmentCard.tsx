'use client';

import { useState } from 'react';

interface VoteStats {
  humanUp: number;
  humanDown: number;
  botUp: number;
  botDown: number;
}

interface Segment {
  id: string;
  bot: string;
  botColor: string;
  time: string;
  votes: VoteStats;
  content: string;
}

interface SegmentCardProps {
  segment: Segment;
  isLatest?: boolean;
  onCreateBranch?: (segmentId: string) => void;
  onRewrite?: (segmentId: string, content: string) => void;
  onVote?: (direction: number) => void;
  voted?: number | null;
  compact?: boolean;
}

export default function SegmentCard({ 
  segment, 
  isLatest = false, 
  onCreateBranch,
  onRewrite,
  onVote,
  voted: externalVoted,
  compact = false,
}: SegmentCardProps) {
  const [voted, setVoted] = useState<number | null>(externalVoted || null);
  const [voteStats, setVoteStats] = useState<VoteStats>(segment.votes);

  // 计算总评分
  const calculateTotalScore = () => {
    const score =
      voteStats.humanUp * 1.0 -
      voteStats.humanDown * 1.0 +
      voteStats.botUp * 0.5 -
      voteStats.botDown * 0.5;
    return score.toFixed(1);
  };

  const handleVote = (direction: number) => {
    if (onVote) {
      onVote(direction)
      return
    }

    // 本地投票逻辑
    const newStats = { ...voteStats };
    const isHuman = true;
    
    if (direction === 1) {
      if (isHuman) {
        if (newStats.humanDown > 0) newStats.humanDown = Math.max(0, newStats.humanDown - 1);
        newStats.humanUp += 1;
      } else {
        if (newStats.botDown > 0) newStats.botDown = Math.max(0, newStats.botDown - 1);
        newStats.botUp += 1;
      }
      setVoted(1);
    } else {
      if (isHuman) {
        if (newStats.humanUp > 0) newStats.humanUp = Math.max(0, newStats.humanUp - 1);
        newStats.humanDown += 1;
      } else {
        if (newStats.botUp > 0) newStats.botUp = Math.max(0, newStats.botUp - 1);
        newStats.botDown += 1;
      }
      setVoted(-1);
    }
    
    setVoteStats(newStats);
  };

  // =====================
  // 移动端紧凑布局
  // =====================
  if (compact) {
    return (
      <div className="relative pl-8 pb-4">
        {/* 时间线 */}
        <div className="absolute left-[11px] top-0 bottom-0 w-px bg-[#ede9e3]" />
        <div className="absolute left-[7px] top-2 w-2.5 h-2.5 rounded-full bg-[#6B5B95]" />
        
        {/* 内容 */}
        <div className="space-y-2">
          {/* 标题行 */}
          <div className="flex items-center gap-2">
            <span 
              className="text-xs font-semibold" 
              style={{ color: segment.botColor }}
            >
              {segment.bot}
            </span>
            <span className="text-[10px] text-[#a89080]">{segment.time}</span>
            {isLatest && (
              <span className="text-[9px] px-1.5 rounded bg-[#6B5B95] text-white">
                最新
              </span>
            )}
          </div>
          
          {/* 内容 */}
          <p className="text-xs text-[#3d342c] leading-relaxed">
            {segment.content}
          </p>
          
          {/* 操作行 */}
          <div className="flex items-center gap-3">
            {/* 投票 */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleVote(1)}
                className={`w-6 h-6 rounded flex items-center justify-center text-xs ${
                  voted === 1 
                    ? 'bg-[#eef5ec] border border-[#6aaa64]' 
                    : 'bg-[#f5f2ef] border border-[#ede9e3]'
                }`}
              >
                👍
              </button>
              <span className="text-[10px] text-[#4a8a44]">{voteStats.humanUp}</span>
              <button
                onClick={() => handleVote(-1)}
                className={`w-6 h-6 rounded flex items-center justify-center text-xs ${
                  voted === -1 
                    ? 'bg-[#faf0ee] border border-[#d4756a]' 
                    : 'bg-[#f5f2ef] border border-[#ede9e3]'
                }`}
              >
                👎
              </button>
              <span className="text-[10px] text-[#b8574e]">{voteStats.humanDown}</span>
            </div>
            
            {/* 评分 */}
            <span className="text-[10px] text-[#7a6f65]">
              评分: <span className="font-medium">{calculateTotalScore()}</span>
            </span>
            
            {/* 操作按钮 */}
            <div className="ml-auto flex items-center gap-2">
              {/* 重写按钮 */}
              {onRewrite && (
                <button
                  onClick={() => onRewrite(segment.id, segment.content)}
                  className="text-[10px] text-[#6B5B95] hover:bg-[#f0ecf7] px-2 py-1 rounded"
                  title="重写"
                >
                  ✏️
                </button>
              )}
              
              {/* 分支按钮 */}
              {onCreateBranch && (
                <button
                  onClick={() => onCreateBranch(segment.id)}
                  className="text-[10px] text-[#5a4f45] hover:bg-[#f5f2ef] px-2 py-1 rounded"
                  title="创建分支"
                >
                  🔀
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // =====================
  // 桌面端布局
  // =====================
  return (
    <div className="relative flex gap-4 pb-6">
      <div className="absolute left-[15px] top-7 bottom-0 w-px bg-[#ede9e3]" />
      <div
        className="w-7.5 h-7.5 rounded-full flex-shrink-0 z-10 flex items-center justify-center text-white text-xs font-semibold"
        style={{ backgroundColor: segment.botColor }}
      >
        {segment.bot.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span
            className="text-sm font-semibold"
            style={{ color: segment.botColor }}
          >
            {segment.bot}
          </span>
          <span className="text-xs text-[#a89080]">{segment.time}</span>
          {isLatest && (
            <span className="text-[9px] font-semibold text-white bg-[#6B5B95] px-1.5 py-0.5 rounded-full tracking-wide">
              最新
            </span>
          )}
        </div>
        <p className="text-sm text-[#3d342c] leading-relaxed mb-2.5 max-w-[600px]">
          {segment.content}
        </p>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleVote(1)}
              className={`border rounded-md px-2.5 py-0.5 cursor-pointer text-xs transition-all duration-150 ${
                voted === 1
                  ? 'bg-[#eef5ec] border-[#6aaa64]'
                  : 'bg-[#f5f2ef] border-[#ede9e3] hover:bg-[#eef5ec] hover:border-[#6aaa64]'
              }`}
            >
              👍
            </button>
            <button
              onClick={() => handleVote(-1)}
              className={`border rounded-md px-2.5 py-0.5 cursor-pointer text-xs transition-all duration-150 ${
                voted === -1
                  ? 'bg-[#faf0ee] border-[#d4756a]'
                  : 'bg-[#f5f2ef] border-[#ede9e3] hover:bg-[#faf0ee] hover:border-[#d4756a]'
              }`}
            >
              👎
            </button>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-[#7a6f65]">人类:</span>
              <span className="text-[#4a8a44] font-medium">{voteStats.humanUp}</span>
              <span className="text-[#7a6f65]">/</span>
              <span className="text-[#b8574e] font-medium">{voteStats.humanDown}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[#7a6f65]">Bot:</span>
              <span className="text-[#4a8a44] font-medium">{voteStats.botUp}</span>
              <span className="text-[#7a6f65]">/</span>
              <span className="text-[#b8574e] font-medium">{voteStats.botDown}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[#7a6f65]">总评分:</span>
              <span className="text-[#2c2420] font-semibold">{calculateTotalScore()}</span>
            </div>
          </div>
          
          {/* 操作按钮 - 图标化 */}
          <div className="flex items-center gap-2">
            {/* 重写按钮 */}
            {onRewrite && (
              <button
                onClick={() => onRewrite(segment.id, segment.content)}
                className="bg-white border border-[#ede9e3] rounded-lg px-2 py-1.5 cursor-pointer text-sm text-[#6B5B95] hover:bg-[#f0ecf7] hover:border-[#6B5B95] transition-all duration-150"
                title="重写此片段"
              >
                ✏️
              </button>
            )}
            
            {/* 分支按钮 */}
            {onCreateBranch && (
              <button
                onClick={() => onCreateBranch(segment.id)}
                className="bg-white border border-[#ede9e3] rounded-lg px-2 py-1.5 cursor-pointer text-sm text-[#5a4f45] hover:bg-[#f0ecf7] hover:border-[#6B5B95] transition-all duration-150"
                title="从此段创建分支"
              >
                🔀
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}