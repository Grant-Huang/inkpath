'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// 懒加载
const DiscussionPanelWithAPI = dynamic(
  () => import('../discussion/DiscussionPanelWithAPI'),
  { ssr: false, loading: () => <div className="animate-pulse bg-gray-100 h-48 rounded-lg"></div> }
);

const CreateBranchModal = dynamic(
  () => import('../branches/CreateBranchModal'),
  { ssr: false }
);

const BranchTree = dynamic(
  () => import('../branches/BranchTree'),
  { ssr: false }
);

const SummaryCard = dynamic(
  () => import('./SummaryCard'),
  { ssr: false }
);

const SegmentCardWithAPI = dynamic(
  () => import('../segments/SegmentCardWithAPI'),
  { ssr: false }
);

const RewriteModal = dynamic(
  () => import('../rewrite/RewriteModal'),
  { ssr: false }
);

const PullToAppend = dynamic<{
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
}>(
  () => import('./NewSegmentsMonitor').then(mod => ({ default: mod.PullToAppend })),
  { ssr: false }
);

interface ReadingViewProps {
  story?: any;
  branches?: any[];
  segments?: any[];
  comments?: any[];
  summary?: any;
  selectedBranchId?: string | null;
  onBranchSelect?: (branchId: string) => void;
  storyId?: string;
  onBack?: () => void;
  // 新片段监测相关
  onPullToAppend?: () => void;
  hasNewContent?: boolean;
  newSegmentsCount?: number;
}

export default function ReadingView({ 
  story, 
  branches = [], 
  segments = [],
  comments = [],
  summary,
  selectedBranchId,
  onBranchSelect,
  storyId,
  onBack,
  onPullToAppend,
  hasNewContent = false,
  newSegmentsCount = 0
}: ReadingViewProps) {
  const [selectedBranch, setSelectedBranch] = useState(selectedBranchId || '');
  const [discussionOpen, setDiscussionOpen] = useState(false);
  const [showCreateBranchModal, setShowCreateBranchModal] = useState(false);
  const [createBranchSegmentId, setCreateBranchSegmentId] = useState<string | null>(null);
  const [showBranches, setShowBranches] = useState(true);
  
  // 重写相关状态
  const [showRewriteModal, setShowRewriteModal] = useState(false);
  const [rewriteSegmentId, setRewriteSegmentId] = useState<string | null>(null);
  const [rewriteContent, setRewriteContent] = useState('');

  // 同步分支状态
  useEffect(() => {
    if (selectedBranchId && selectedBranchId !== selectedBranch) {
      setSelectedBranch(selectedBranchId)
    }
  }, [selectedBranchId, selectedBranch])

  // 转换分支数据
  const transformedBranches = (branches || []).map((branch: any) => ({
    id: branch.id,
    label: branch.title || branch.label || '未命名分支',
    segments: branch.segments_count || branch.segments || 0,
    bots: branch.active_bots_count || branch.bots || 0,
    isMain: !branch.parent_branch_id && !branch.parentId,
    parentId: branch.parent_branch_id || branch.parentId || null,
    forkAt: branch.fork_at_segment_order || branch.forkAt,
  }))

  // 移动端处理分支选择
  const handleBranchSelect = (branchId: string) => {
    setSelectedBranch(branchId)
    if (onBranchSelect) {
      onBranchSelect(branchId)
    }
    setShowBranches(false) // 移动端选择后折叠
  }

  // =====================
  // 移动端布局 - 单主线 + 折叠结构
  // =====================
  return (
    <div className="lg:max-w-[1080px] lg:mx-auto lg:px-6 lg:py-10">
      
      {/* ===================== */}
      {/* 移动端：顶部栏 */}
      {/* ===================== */}
      <div className="lg:hidden sticky top-0 bg-white/95 backdrop-blur-sm z-10 border-b border-[#ede9e3]">
        {/* 标题行 */}
        <div className="flex items-center justify-between px-4 py-3">
          <button onClick={onBack} className="text-[#6B5B95]">
            ← 返回
          </button>
          <h1 className="text-base font-bold text-[#2c2420] truncate max-w-[200px]">
            {story?.title || '加载中...'}
          </h1>
        </div>
        
        {/* 折叠式分支选择 */}
        <details 
          className="border-t border-[#ede9e3]"
          open={showBranches}
          onToggle={(e) => setShowBranches((e.target as HTMLDetailsElement).open)}
        >
          <summary className="flex items-center justify-between px-4 py-2 cursor-pointer list-none">
            <span className="text-xs text-[#5a4f45]">
              📍 {transformedBranches.find(b => b.id === selectedBranch)?.label || '选择分支'}
            </span>
            <span className="text-xs text-[#a89080]">▼</span>
          </summary>
          <div className="px-4 pb-3">
            <BranchTree
              branches={transformedBranches}
              selectedBranch={selectedBranch || selectedBranchId || ''}
              onSelect={handleBranchSelect}
              onCreateBranch={() => setShowCreateBranchModal(true)}
              compact
            />
          </div>
        </details>
      </div>

      {/* ===================== */}
      {/* 移动端：主要内容区 */}
      {/* ===================== */}
      <div className="lg:hidden px-4 py-4 space-y-4">
        {/* 摘要 */}
        {summary && (
          <details className="rounded-lg border border-[#ede9e3] overflow-hidden">
            <summary className="px-3 py-2 bg-[#f5f2ef] text-xs text-[#5a4f45] cursor-pointer list-none flex items-center justify-between">
              <span>📌 当前进展摘要</span>
              <span>▼</span>
            </summary>
            <div className="px-3 py-2 text-xs text-[#7a6f65]">
              {(summary.summary || summary.current_summary || '').slice(0, 100)}...
            </div>
          </details>
        )}

        {/* 续写内容 */}
        <div className="space-y-3">
          {(segments || []).map((segment: any, i: number) => (
            <SegmentCardWithAPI
              key={segment.id || i}
              segment={segment}
              isLatest={i === (segments?.length || 0) - 1}
              onCreateBranch={(segmentId: string) => {
                setCreateBranchSegmentId(segmentId);
                setShowCreateBranchModal(true);
              }}
              compact
            />
          ))}
        </div>

        {/* 上拉加载更多 */}
        <PullToAppend 
          hasMore={hasNewContent || newSegmentsCount > 0}
          loading={false}
          onLoadMore={onPullToAppend || (() => {})}
        />

        {/* 底部操作栏 */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#ede9e3] px-4 py-3 flex gap-2 z-20">
          <button
            onClick={() => setDiscussionOpen(!discussionOpen)}
            className="flex-1 border border-[#ede9e3] rounded-lg px-3 py-2 text-xs text-[#5a4f45] bg-white"
          >
            💬 讨论
          </button>
          <button
            onClick={() => {
              setCreateBranchSegmentId(null);
              setShowCreateBranchModal(true);
            }}
            className="flex-1 bg-[#6B5B95] text-white rounded-lg px-3 py-2 text-xs font-medium"
          >
            🔀 创建分支
          </button>
        </div>

        {/* 讨论区 */}
        {discussionOpen && selectedBranchId && (
          <div className="pb-16">
            <DiscussionPanelWithAPI branchId={selectedBranchId} comments={comments} />
          </div>
        )}
      </div>

      {/* ===================== */}
      {/* ===================== */}
      {/* 桌面端：保持原布局 */}
      {/* ===================== */}
      {/* ===================== */}
      
      <div className="hidden lg:flex gap-12">
        {/* 分支树 */}
        <BranchTree
          branches={transformedBranches}
          selectedBranch={selectedBranch || selectedBranchId || ''}
          onSelect={handleBranchSelect}
          onCreateBranch={() => setShowCreateBranchModal(true)}
        />

        {/* 主内容 */}
        <div className="flex-1 min-w-0">
          {/* 标题区 */}
          <div className="mb-7">
            <div className="flex items-center gap-2.5 mb-1">
              {story?.genre && (
                <span className="text-xs font-semibold text-[#6B5B95] bg-[#f0ecf7] px-2.5 py-0.5 rounded-full">
                  {story.genre}
                </span>
              )}
              <span className="text-xs text-[#a89080]">
                {transformedBranches.reduce((acc: number, b: any) => acc + b.segments, 0)} 段续写 · {transformedBranches.reduce((acc: number, b: any) => acc + b.bots, 0)} Bot
              </span>
            </div>
            <h1 className="text-2xl serif font-bold text-[#2c2420] mb-1 tracking-tight">
              {story?.title || '故事标题'}
            </h1>
          </div>

          {/* 摘要 */}
          {summary && (
            <SummaryCard
              summary={summary.summary || summary.current_summary || ''}
              coversUpTo={summary.covers_up_to || summary.summary_covers_up_to || 0}
              updatedAt={summary.updated_at || summary.summary_updated_at || '未知'}
            />
          )}

          {/* 续写列表 */}
          <div className="mb-6 space-y-0">
            {(segments || []).map((segment: any, i: number) => (
              <SegmentCardWithAPI
                key={segment.id || i}
                segment={segment}
                isLatest={i === (segments?.length || 0) - 1}
              onCreateBranch={(segmentId: string) => {
                console.log('onCreateBranch called:', { segmentId, storyId })
                setCreateBranchSegmentId(segmentId);
                setShowCreateBranchModal(true);
              }}
              onRewrite={(segmentId: string, content: string) => {
                console.log('onRewrite called:', { segmentId, contentLength: content.length })
                setRewriteSegmentId(segmentId);
                setRewriteContent(content);
                setShowRewriteModal(true);
              }}
              />
            ))}
          </div>

          {/* 桌面端：底部点击加载新续写 */}
          {newSegmentsCount > 0 && (
            <div className="hidden lg:flex mt-6 py-4 px-4 rounded-lg border border-[#ede9e3] bg-[#faf8f6] justify-center">
              <button
                type="button"
                onClick={() => onPullToAppend?.()}
                className="text-[#6B5B95] hover:text-[#5a4a84] font-medium text-sm"
              >
                下面有 {newSegmentsCount} 条新续写，点击加载
              </button>
            </div>
          )}

          {/* 已移除底部讨论区和创建分支按钮 - 功能移至片段图标 */}
        </div>
      </div>

      {/* 创建分支弹窗 */}
      {/* 创建分支Modal - 添加调试 */}
      {showCreateBranchModal && storyId ? (
        <CreateBranchModal 
          onClose={() => {
            console.log('Closing CreateBranchModal')
            setShowCreateBranchModal(false);
            setCreateBranchSegmentId(null);
          }}
          storyId={storyId}
          segmentId={createBranchSegmentId}
          branchId={selectedBranch}
        />
      ) : showCreateBranchModal && !storyId ? (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg">
            <p className="text-red-500">错误：缺少 storyId</p>
            <button 
              onClick={() => setShowCreateBranchModal(false)}
              className="mt-4 px-4 py-2 bg-gray-500 text-white rounded"
            >
              关闭
            </button>
          </div>
        </div>
      ) : null}

      {/* 重写弹窗 */}
      {showRewriteModal && rewriteSegmentId ? (
        <RewriteModal
          segmentId={rewriteSegmentId}
          segmentContent={rewriteContent}
          onClose={() => {
            console.log('Closing RewriteModal')
            setShowRewriteModal(false);
            setRewriteSegmentId(null);
          }}
        />
      ) : showRewriteModal && !rewriteSegmentId ? (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg">
            <p className="text-red-500">错误：缺少 rewriteSegmentId</p>
            <button 
              onClick={() => setShowRewriteModal(false)}
              className="mt-4 px-4 py-2 bg-gray-500 text-white rounded"
            >
              关闭
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
