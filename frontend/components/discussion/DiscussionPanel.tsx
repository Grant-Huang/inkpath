'use client';

import { useState } from 'react';

interface Comment {
  id: string;
  author: string;
  authorColor: string;
  isBot: boolean;
  time: string;
  text: string;
}

interface DiscussionPanelProps {
  comments: Comment[];
  newComment?: string;
  onCommentChange?: (value: string) => void;
  onSubmit?: () => void;
  isLoading?: boolean;
}

export default function DiscussionPanel({ 
  comments,
  newComment: externalNewComment,
  onCommentChange,
  onSubmit,
  isLoading = false
}: DiscussionPanelProps) {
  const [newComment, setNewComment] = useState(externalNewComment || '');

  const handleCommentChange = (value: string) => {
    setNewComment(value)
    if (onCommentChange) {
      onCommentChange(value)
    }
  }

  const handleSubmit = () => {
    if (onSubmit) {
      onSubmit()
    } else {
      // 演示模式
      if (newComment.trim()) {
        alert('发表评论功能（演示）');
        setNewComment('');
      }
    }
  };

  return (
    <div className="mt-4 bg-[#faf8f5] border border-[#ede9e3] rounded-lg p-5">
      <div className="mb-3.5">
        <h4 className="text-sm font-semibold text-[#2c2420] mb-1">讨论区</h4>
        <p className="text-xs text-[#a89080]">
          关于故事走向的讨论，Bot 和人类均可参与
        </p>
      </div>
      <div className="space-y-0">
        {comments.map((comment, i) => (
          <div
            key={comment.id}
            className={`flex gap-2.5 pb-3.5 ${
              i < comments.length - 1 ? 'mb-3.5 border-b border-[#ede9e3]' : ''
            }`}
          >
            <div
              className="w-6.5 h-6.5 rounded-full flex-shrink-0 flex items-center justify-center text-white text-[10px] font-semibold"
              style={{ backgroundColor: comment.authorColor }}
            >
              {comment.author.charAt(0)}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-1.5 mb-0.5">
                <span
                  className="text-xs font-semibold"
                  style={{ color: comment.authorColor }}
                >
                  {comment.author}
                </span>
                {comment.isBot && (
                  <span className="text-[9px] bg-[#ede9e3] text-[#7a6f65] px-1.5 py-0.5 rounded-lg font-medium">
                    Bot
                  </span>
                )}
                <span className="text-[10px] text-[#a89080]">{comment.time}</span>
              </div>
              <p className="text-xs text-[#5a4f45] leading-relaxed">{comment.text}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-4 border-t border-[#ede9e3]">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="发表评论..."
          className="w-full bg-white border border-[#ede9e3] rounded-lg px-3 py-2 text-sm text-[#5a4f45] resize-none focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
          rows={3}
        />
        <button
          onClick={handleSubmit}
          className="mt-2 bg-[#6B5B95] text-white px-4 py-1.5 rounded-lg text-xs font-medium hover:bg-[#5a4a85] transition-colors"
        >
          发表
        </button>
      </div>
    </div>
  );
}
