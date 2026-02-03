'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { branchesApi } from '@/lib/api';

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
  onBack 
}: ReadingViewProps) {
  const [selectedBranch, setSelectedBranch] = useState(selectedBranchId || '');
  const [discussionOpen, setDiscussionOpen] = useState(false);
  const [showCreateBranchModal, setShowCreateBranchModal] = useState(false);
  const [createBranchSegmentId, setCreateBranchSegmentId] = useState<string | null>(null);
  const [showBranches, setShowBranches] = useState(true);
  const [showParticipants, setShowParticipants] = useState(false);

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
          <button 
            onClick={() => setShowParticipants(!showParticipants)}
            className="w-8 h-8 rounded-full bg-[#f0ecf7] flex items-center justify-center text-[#6B5B95]"
          >
            👥
          </button>
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
      {/* 参与者弹窗（移动端） */}
      {/* ===================== */}
      {showParticipants && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-50"
          onClick={() => setShowParticipants(false)}
        >
          <div 
            className="absolute right-0 top-0 bottom-0 w-80 bg-white p-4 overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-[#2c2420]">参与者</h3>
              <button onClick={() => setShowParticipants(false)}>✕</button>
            </div>
            {/* 参与者列表 */}
            <ParticipantList branchId={(selectedBranch || selectedBranchId) || undefined} compact />
          </div>
        </div>
      )}

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
              <span className="text-xs font-semibold text-[#6B5B95] bg-[#f0ecf7] px-2.5 py-0.5 rounded-full">
                科幻
              </span>
              <span className="text-xs text-[#a89080]">
                {transformedBranches.reduce((acc: number, b: any) => acc + b.segments, 0)} 段续写 · {transformedBranches.reduce((acc: number, b: any) => acc + b.bots, 0)} Bot
              </span>
            </div>
            <h1 className="text-2xl serif font-bold text-[#2c2420] mb-1 tracking-tight">
              {story?.title || '故事标题'}
            </h1>
            <p className="text-sm text-[#7a6f65]">
              {story?.background || '故事背景'}
            </p>
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
                  setCreateBranchSegmentId(segmentId);
                  setShowCreateBranchModal(true);
                }}
              />
            ))}
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 pt-5 border-t border-[#ede9e3]">
            <button
              onClick={() => setDiscussionOpen(!discussionOpen)}
              className={`border rounded-lg px-4 py-2 cursor-pointer text-sm font-medium transition-all duration-150 ${
                discussionOpen
                  ? 'bg-[#f0ecf7] border-[#6B5B95] text-[#6B5B95]'
                  : 'bg-white border-[#ede9e3] text-[#5a4f45] hover:bg-[#f0ecf7] hover:border-[#6B5B95] hover:text-[#6B5B95]'
              }`}
            >
              💬 讨论区 {discussionOpen ? '▲' : '▼'}
            </button>
            <button
              onClick={() => {
                setCreateBranchSegmentId(null);
                setShowCreateBranchModal(true);
              }}
              className="bg-white border border-[#ede9e3] rounded-lg px-4 py-2 cursor-pointer text-sm text-[#5a4f45] font-medium transition-all duration-150 hover:bg-[#f0ecf7] hover:border-[#6B5B95] hover:text-[#6B5B95]"
            >
              🔀 创建分支（选择分叉点）
            </button>
          </div>

          {/* 讨论区 */}
          {discussionOpen && selectedBranchId && (
            <DiscussionPanelWithAPI branchId={selectedBranchId} comments={comments} />
          )}
        </div>

        {/* 参与者侧边栏 */}
        <div className="w-60 flex-shrink-0 mt-7 pt-5 border-t border-[#ede9e3]">
          <ParticipantList branchId={(selectedBranch || selectedBranchId) || undefined} />
        </div>
      </div>

      {/* 创建分支弹窗 */}
      {showCreateBranchModal && storyId && (
        <CreateBranchModal 
          onClose={() => {
            setShowCreateBranchModal(false);
            setCreateBranchSegmentId(null);
          }}
          storyId={storyId}
          segmentId={createBranchSegmentId}
          branchId={selectedBranch}
        />
      )}
    </div>
  );
}

// 参与者列表组件
function ParticipantList({ branchId, compact = false }: { branchId?: string; compact?: boolean }) {
  const [participants, setParticipants] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!branchId) {
      setLoading(false)
      return
    }

    const fetchParticipants = async () => {
      try {
        const response = await branchesApi.participants(branchId)
        if (response.data?.participants) {
          setParticipants(response.data.participants)
        }
      } catch (error) {
        console.error('获取参与者失败:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchParticipants()
  }, [branchId])

  // 角色翻译
  const roleTranslations: Record<string, string> = {
    narrator: '叙述者',
    challenger: '挑衅者',
    voice: '声音',
    participant: '参与者',
  }

  // 角色颜色映射
  const roleColors: Record<string, string> = {
    叙述者: 'bg-[#f0ecf7] text-[#6B5B95]',
    挑衅者: 'bg-[#faf0ee] text-[#E07A5F]',
    声音: 'bg-[#e8f0f7] text-[#3D5A80]',
    participant: 'bg-[#ede9e3] text-[#7a6f65]',
  }

  // Bot 颜色生成
  const getBotColor = (name: string) => {
    const colors = ['#6B5B95', '#E07A5F', '#3D5A80', '#5A7BA0', '#7A9E9F', '#9B7BA0', '#B8860B']
    const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[hash % colors.length]
  }

  if (loading) {
    return (
      <div className={compact ? 'space-y-2' : 'space-y-1.5'}>
        <h3 className="text-xs font-semibold text-[#a89080] uppercase tracking-wider mb-3">
          参与者
        </h3>
        <div className="text-xs text-[#a89080]">加载中...</div>
      </div>
    )
  }

  return (
    <div className={compact ? 'space-y-2' : 'space-y-1.5'}>
      <h3 className="text-xs font-semibold text-[#a89080] uppercase tracking-wider mb-3">
        参与者 {participants.length > 0 && `(${participants.length})`}
      </h3>
      {participants.length === 0 ? (
        <div className="text-xs text-[#a89080]">暂无参与者</div>
      ) : (
        participants.map((p) => (
          <div key={p.id} className="flex items-center gap-2">
            <div
              className={`${compact ? 'w-6 h-6' : 'w-5.5 h-5.5'} rounded-full flex items-center justify-center text-white text-xs font-semibold relative`}
              style={{ backgroundColor: getBotColor(p.name) }}
            >
              {p.name.charAt(0)}
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 border-2 border-white rounded-full flex items-center justify-center">
                <span className="text-[6px]">{p.type === 'bot' ? '🤖' : '👤'}</span>
              </span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-1">
                <span className={`${compact ? 'text-xs' : 'text-xs'} font-medium text-[#3d342c]`}>
                  {p.name}
                </span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${
                  roleColors[roleTranslations[p.role] || roleColors.participant]
                }`}>
                  {roleTranslations[p.role] || p.role || '参与者'}
                </span>
              </div>
              <div className={`${compact ? 'text-[10px]' : 'text-[10px]'} text-[#a89080]`}>
                {p.type === 'bot' ? p.model : '人类参与者'}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
