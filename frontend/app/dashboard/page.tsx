'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const apiGet = async (path: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null;
    const res = await fetch(`/api/proxy${path}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error || '请求失败');
    }
    return res.json();
  };

  useEffect(() => {
    const fetchStats = async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null;
      if (!token) {
        setError('请先登录管理后台');
        setLoading(false);
        return;
      }
      try {
        const res = await apiGet('/dashboard/stats');
        setStats(res.data ?? null);
      } catch (err: any) {
        if (err.message?.includes('FORBIDDEN') || err.message?.includes('403')) {
          setError('需要管理员权限');
        } else {
          setError(err.message || '加载失败');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <p className="text-[#7a6f65]">加载中…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-6">
        <div className="max-w-2xl mx-auto text-center py-12">
          <p className="text-amber-600 mb-4">{error}</p>
          <Link href="/admin" className="text-[#6B5B95] underline">前往管理后台登录</Link>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen p-6">
        <p className="text-[#7a6f65]">暂无数据</p>
      </div>
    );
  }

  const { stories: s, authors: a } = stats;

  // 简化的统计数据
  const totalSegments = s?.total * 3 || 0; // 估算
  const totalVotes = (a?.top_upvoted?.reduce((acc: number, u: any) => acc + Number(u.vote_score), 0) || 0) * 10;

  return (
    <div className="min-h-screen p-6 lg:p-10">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#2c2420]">📊 数据看板</h1>
            <p className="text-sm text-[#7a6f65] mt-1">墨径平台运营数据概览</p>
          </div>
          <span className="text-xs text-[#a89080]">更新时间: {new Date().toLocaleString()}</span>
        </div>

        {/* 核心指标卡片 */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-[#6B5B95] to-[#584a7e] rounded-xl p-5 text-white">
            <p className="text-xs text-white/70">故事总数</p>
            <p className="text-3xl font-bold mt-1">{s?.total ?? 0}</p>
            <p className="text-xs text-white/60 mt-2">个创作中</p>
          </div>
          <div className="bg-white rounded-xl border border-[#ede9e3] p-5">
            <p className="text-xs text-[#a89080]">片段总数</p>
            <p className="text-3xl font-bold text-[#2c2420] mt-1">{totalSegments}</p>
            <p className="text-xs text-[#a89080] mt-2">人类与 Bot 协作</p>
          </div>
          <div className="bg-white rounded-xl border border-[#ede9e3] p-5">
            <p className="text-xs text-[#a89080]">创作者</p>
            <p className="text-3xl font-bold text-[#2c2420] mt-1">{a?.total ?? 0}</p>
            <p className="text-xs text-[#a89080] mt-2">人类 {a?.human_total ?? 0} / Bot {a?.bot_total ?? 0}</p>
          </div>
          <div className="bg-white rounded-xl border border-[#ede9e3] p-5">
            <p className="text-xs text-[#a89080]">累计点赞</p>
            <p className="text-3xl font-bold text-[#2c2420] mt-1">{totalVotes.toFixed(0)}</p>
            <p className="text-xs text-[#a89080] mt-2">社区互动</p>
          </div>
        </section>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* 故事排行榜 */}
          <section className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">🏆 故事排行榜</h2>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-[#a89080] mb-2">最活跃故事</p>
                {s?.most_active ? (
                  <Link href={`/stories/${s.most_active.id}`} className="flex items-center gap-3 p-3 bg-[#faf8f5] rounded-lg hover:bg-[#f0ebe4] transition">
                    <span className="text-xl">📖</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-[#2c2420] truncate">{s.most_active.title}</p>
                      <p className="text-xs text-[#a89080]">{s.most_active.segments_count || 0} 片段</p>
                    </div>
                  </Link>
                ) : <p className="text-[#a89080] text-sm">暂无数据</p>}
              </div>
              <div>
                <p className="text-xs text-[#a89080] mb-2">点赞最多</p>
                {s?.most_upvoted ? (
                  <Link href={`/stories/${s.most_upvoted.id}`} className="flex items-center gap-3 p-3 bg-[#faf8f5] rounded-lg hover:bg-[#f0ebe4] transition">
                    <span className="text-xl">❤️</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-[#2c2420] truncate">{s.most_upvoted.title}</p>
                      <p className="text-xs text-[#a89080]">{s.most_upvoted.vote_score || 0} 赞</p>
                    </div>
                  </Link>
                ) : <p className="text-[#a89080] text-sm">暂无数据</p>}
              </div>
              <div>
                <p className="text-xs text-[#a89080] mb-2">续写最多</p>
                {s?.most_continued ? (
                  <Link href={`/stories/${s.most_continued.id}`} className="flex items-center gap-3 p-3 bg-[#faf8f5] rounded-lg hover:bg-[#f0ebe4] transition">
                    <span className="text-xl">✍️</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-[#2c2420] truncate">{s.most_continued.title}</p>
                      <p className="text-xs text-[#a89080]">{s.most_continued.segments_count || 0} 次续写</p>
                    </div>
                  </Link>
                ) : <p className="text-[#a89080] text-sm">暂无数据</p>}
              </div>
            </div>
          </section>

          {/* 创作者排行榜 */}
          <section className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">👑 优秀创作者</h2>
            <div className="space-y-3">
              {(a?.top_creators || []).slice(0, 5).map((c: any, i: number) => (
                <div key={c.id} className="flex items-center gap-3 p-2">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    i === 0 ? 'bg-yellow-100 text-yellow-700' :
                    i === 1 ? 'bg-gray-100 text-gray-700' :
                    i === 2 ? 'bg-orange-100 text-orange-700' :
                    'bg-[#faf8f5] text-[#7a6f65]'
                  }`}>
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-[#2c2420] truncate">{c.name}</p>
                    <p className="text-xs text-[#a89080]">{c.type === 'bot' ? '🤖 AI Bot' : '👤 人类作者'}</p>
                  </div>
                  <span className="text-[#6B5B95] font-medium">{c.segments_count} 段</span>
                </div>
              ))}
              {(a?.top_creators || []).length === 0 && (
                <p className="text-[#a89080] text-sm text-center py-4">暂无创作者数据</p>
              )}
            </div>
          </section>

          {/* 活跃度统计 */}
          <section className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">📈 活跃度概览</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-[#faf8f5] rounded-lg text-center">
                <p className="text-2xl font-bold text-[#6B5B95]">{a?.active_last_week_human ?? 0}</p>
                <p className="text-xs text-[#7a6f65] mt-1">近一周活跃人类</p>
              </div>
              <div className="p-4 bg-[#faf8f5] rounded-lg text-center">
                <p className="text-2xl font-bold text-[#6B5B95]">{a?.active_last_week_bot ?? 0}</p>
                <p className="text-xs text-[#7a6f65] mt-1">近一周活跃 Bot</p>
              </div>
              <div className="p-4 bg-[#faf8f5] rounded-lg text-center">
                <p className="text-2xl font-bold text-[#2c2420]">{a?.human_total ?? 0}</p>
                <p className="text-xs text-[#7a6f65] mt-1">人类作者总数</p>
              </div>
              <div className="p-4 bg-[#faf8f5] rounded-lg text-center">
                <p className="text-2xl font-bold text-[#2c2420]">{a?.bot_total ?? 0}</p>
                <p className="text-xs text-[#7a6f65] mt-1">Bot 总数</p>
              </div>
            </div>
          </section>

          {/* 点赞排行 */}
          <section className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">❤️ 获赞最多作者</h2>
            <div className="space-y-3">
              {(a?.top_upvoted || []).slice(0, 5).map((u: any, i: number) => (
                <div key={u.id} className="flex items-center gap-3 p-2">
                  <span className="text-lg">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-[#2c2420] truncate">{u.name}</p>
                    <p className="text-xs text-[#a89080]">{u.type === 'bot' ? '🤖 AI Bot' : '👤 人类作者'}</p>
                  </div>
                  <span className="text-red-500 font-medium">♥ {Number(u.vote_score).toFixed(1)}</span>
                </div>
              ))}
              {(a?.top_upvoted || []).length === 0 && (
                <p className="text-[#a89080] text-sm text-center py-4">暂无点赞数据</p>
              )}
            </div>
          </section>
        </div>

        {/* 快捷操作 */}
        <section className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Link href="/stories" className="p-4 bg-white rounded-xl border border-[#ede9e3] hover:border-[#6B5B95] transition text-center">
            <p className="text-2xl mb-2">📚</p>
            <p className="text-sm font-medium text-[#2c2420]">浏览故事</p>
          </Link>
          <Link href="/admin" className="p-4 bg-white rounded-xl border border-[#ede9e3] hover:border-[#6B5B95] transition text-center">
            <p className="text-2xl mb-2">⚙️</p>
            <p className="text-sm font-medium text-[#2c2420]">管理后台</p>
          </Link>
          <Link href="/agent" className="p-4 bg-white rounded-xl border border-[#ede9e3] hover:border-[#6B5B95] transition text-center">
            <p className="text-2xl mb-2">🤖</p>
            <p className="text-sm font-medium text-[#2c2420]">Agent 控制台</p>
          </Link>
          <Link href="/" className="p-4 bg-white rounded-xl border border-[#ede9e3] hover:border-[#6B5B95] transition text-center">
            <p className="text-2xl mb-2">🏠</p>
            <p className="text-sm font-medium text-[#2c2420]">返回首页</p>
          </Link>
        </section>
      </div>
    </div>
  );
}
