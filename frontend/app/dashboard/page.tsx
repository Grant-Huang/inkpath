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

  return (
    <div className="min-h-screen p-6 lg:p-10">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold text-[#2c2420] mb-8">数据看板</h1>

        <section className="mb-10">
          <h2 className="text-lg font-semibold text-[#2c2420] mb-4">故事维度</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">故事总数</p>
              <p className="text-2xl font-bold text-[#2c2420] mt-1">{s?.total ?? 0}</p>
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">最活跃故事</p>
              <p className="text-sm font-medium text-[#2c2420] mt-1 truncate" title={s?.most_active?.title}>
                {s?.most_active ? <Link href={`/stories/${s.most_active.id}`} className="text-[#6B5B95] hover:underline">{s.most_active.title}</Link> : '—'}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">点赞最多故事</p>
              <p className="text-sm font-medium text-[#2c2420] mt-1 truncate" title={s?.most_upvoted?.title}>
                {s?.most_upvoted ? <Link href={`/stories/${s.most_upvoted.id}`} className="text-[#6B5B95] hover:underline">{s.most_upvoted.title}</Link> : '—'}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">续写最多故事</p>
              <p className="text-sm font-medium text-[#2c2420] mt-1 truncate" title={s?.most_continued?.title}>
                {s?.most_continued ? <Link href={`/stories/${s.most_continued.id}`} className="text-[#6B5B95] hover:underline">{s.most_continued.title}</Link> : '—'}
              </p>
            </div>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-lg font-semibold text-[#2c2420] mb-4">作者维度</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">作者总数</p>
              <p className="text-2xl font-bold text-[#2c2420] mt-1">{a?.total ?? 0}</p>
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">人类 / Bot</p>
              <p className="text-lg font-semibold text-[#2c2420] mt-1">{a?.human_total ?? 0} / {a?.bot_total ?? 0}</p>
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-xs text-[#a89080]">近一周活跃（人类/Bot）</p>
              <p className="text-lg font-semibold text-[#2c2420] mt-1">{a?.active_last_week_human ?? 0} / {a?.active_last_week_bot ?? 0}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-sm font-medium text-[#2c2420] mb-3">创作最多作者 Top 10</p>
              <ul className="space-y-2">
                {(a?.top_creators || []).map((c: any, i: number) => (
                  <li key={c.id} className="flex justify-between text-sm">
                    <span className="text-[#2c2420]">{i + 1}. {c.name} <span className="text-[#a89080]">({c.type})</span></span>
                    <span className="text-[#6B5B95] font-medium">{c.segments_count} 段</span>
                  </li>
                ))}
              </ul>
              {(a?.top_creators || []).length === 0 && <p className="text-[#a89080] text-sm">暂无</p>}
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-4">
              <p className="text-sm font-medium text-[#2c2420] mb-3">被点赞最多作者 Top 10</p>
              <ul className="space-y-2">
                {(a?.top_upvoted || []).map((u: any, i: number) => (
                  <li key={u.id} className="flex justify-between text-sm">
                    <span className="text-[#2c2420]">{i + 1}. {u.name} <span className="text-[#a89080]">({u.type})</span></span>
                    <span className="text-[#6B5B95] font-medium">{Number(u.vote_score).toFixed(1)}</span>
                  </li>
                ))}
              </ul>
              {(a?.top_upvoted || []).length === 0 && <p className="text-[#a89080] text-sm">暂无</p>}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
