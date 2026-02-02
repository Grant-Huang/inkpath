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
}

export default function SegmentCard({ segment, isLatest = false, onCreateBranch }: SegmentCardProps) {
  const [voted, setVoted] = useState<number | null>(null);
  const [voteStats, setVoteStats] = useState<VoteStats>(segment.votes);

  // 计算总评分：人类权重1.0，Bot权重0.5（平均）
  const calculateTotalScore = () => {
    const humanWeight = 1.0;
    const botWeight = 0.5; // 实际应该是0.3-0.8，这里用平均值
    const score =
      voteStats.humanUp * humanWeight -
      voteStats.humanDown * humanWeight +
      voteStats.botUp * botWeight -
      voteStats.botDown * botWeight;
    return score.toFixed(1);
  };

  const handleVote = (direction: number) => {
    // 假设当前用户是人类，实际应该从用户状态获取
    const isHuman = true;
    
    if (isHuman) {
      const newStats = { ...voteStats };
      
      if (direction === 1) {
        // 点赞：如果之前点过踩，先取消点踩
        if (newStats.humanDown > 0) {
          newStats.humanDown = Math.max(0, newStats.humanDown - 1);
        }
        newStats.humanUp += 1;
        setVoted(1);
      } else {
        // 点踩：如果之前点过赞，先取消点赞
        if (newStats.humanUp > 0) {
          newStats.humanUp = Math.max(0, newStats.humanUp - 1);
        }
        newStats.humanDown += 1;
        setVoted(-1);
      }
      
      setVoteStats(newStats);
    } else {
      // Bot投票逻辑（如果需要）
      const newStats = { ...voteStats };
      
      if (direction === 1) {
        if (newStats.botDown > 0) {
          newStats.botDown = Math.max(0, newStats.botDown - 1);
        }
        newStats.botUp += 1;
        setVoted(1);
      } else {
        if (newStats.botUp > 0) {
          newStats.botUp = Math.max(0, newStats.botUp - 1);
        }
        newStats.botDown += 1;
        setVoted(-1);
      }
      
      setVoteStats(newStats);
    }
  };

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
          {onCreateBranch && (
            <button
              onClick={() => onCreateBranch(segment.id)}
              className="bg-white border border-[#ede9e3] rounded-lg px-3 py-1.5 cursor-pointer text-xs text-[#5a4f45] font-medium transition-all duration-150 hover:bg-[#f0ecf7] hover:border-[#6B5B95] hover:text-[#6B5B95]"
            >
              🔀 从此段创建分支
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
