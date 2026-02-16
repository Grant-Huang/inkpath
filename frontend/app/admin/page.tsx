'use client';

import { useState, useEffect } from 'react';

type Tab = 'export' | 'segments' | 'users' | 'logs';

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [tab, setTab] = useState<Tab>('export');
  const [stories, setStories] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [bots, setBots] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [segmentBranchId, setSegmentBranchId] = useState('');
  const [segments, setSegments] = useState<any[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null;
    setToken(t);
  }, []);

  const getToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('jwt_token');
    }
    return null;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem('jwt_token', data.access_token);
        setToken(data.access_token);
      } else {
        setLoginError(data.error || '登录失败');
      }
    } catch (err: any) {
      setLoginError(err.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 代理 API 调用
  const apiGet = async (path: string) => {
    const token = getToken();
    const res = await fetch(`/api/proxy${path}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.error || '请求失败');
    }
    return res.json();
  };

  const apiPatch = async (path: string, body: any) => {
    const token = getToken();
    const res = await fetch(`/api/proxy${path}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.error || '请求失败');
    }
    return res.json();
  };

  const apiDelete = async (path: string) => {
    const token = getToken();
    const res = await fetch(`/api/proxy${path}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.error || '请求失败');
    }
    return res.json();
  };

  const loadStories = async () => {
    const data = await apiGet('/stories?limit=100');
    setStories(data.data?.stories || []);
  };

  const loadUsers = async () => {
    const data = await apiGet('/admin/users');
    setUsers(data.data?.users || []);
  };

  const loadBots = async () => {
    const data = await apiGet('/admin/bots');
    setBots(data.data?.bots || []);
  };

  const loadSegments = async () => {
    if (!segmentBranchId.trim()) return;
    const data = await apiGet(`/branches/${segmentBranchId.trim()}/segments`);
    setSegments(data.data?.segments || []);
  };

  useEffect(() => {
    if (!token) return;
    if (tab === 'export') loadStories();
    if (tab === 'users') {
      loadUsers();
      loadBots();
    }
  }, [token, tab]);

  const handleExport = async (storyId: string, format: 'md' | 'word' | 'pdf') => {
    try {
      const token = getToken();
      if (!token) {
        alert('请先登录');
        return;
      }
      
      const response = await fetch(`/api/proxy/admin/stories/${storyId}/export?format=${format}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error?.error || `导出失败: ${response.status}`);
      }

      const story = stories.find((s: any) => s.id === storyId);
      const baseName = (story?.title || storyId).replace(/[/\\?%*:|"<>]/g, '_').slice(0, 50);
      const ext = format === 'md' ? '.md' : format === 'word' ? '.docx' : '.pdf';
      const blob = await response.blob();
      
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = baseName + ext;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err: any) {
      alert(err.message || '导出失败');
    }
  };

  const handleSaveSegment = async (segmentId: string) => {
    try {
      await apiPatch(`/admin/segments/${segmentId}`, { content: editContent });
      setEditingId(null);
      loadSegments();
    } catch (err: any) {
      alert(err.message || '保存失败');
    }
  };

  const handleDeleteSegment = async (segmentId: string) => {
    if (!confirm('确定删除该片段？')) return;
    try {
      await apiDelete(`/admin/segments/${segmentId}`);
      loadSegments();
    } catch (err: any) {
      alert(err.message || '删除失败');
    }
  };

  const handleBotStatus = async (botId: string, status: string) => {
    try {
      await apiPatch(`/admin/bots/${botId}`, { status });
      loadBots();
    } catch (err: any) {
      alert(err.message || '更新失败');
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen p-8 flex justify-center items-start">
        <div className="w-full max-w-sm bg-white rounded-xl border border-[#ede9e3] p-6 shadow-sm">
          <h1 className="text-xl font-bold text-[#2c2420] mb-4">管理后台登录</h1>
          <p className="text-sm text-[#7a6f65] mb-4">
            邮箱: jacer.huang@gmail.com<br/>
            密码: 80fd7e9b-27ae-4704-8789-0202b8fe6739
          </p>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="email"
              placeholder="邮箱"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              className="w-full px-3 py-2 border border-[#ede9e3] rounded-lg text-sm"
              required
            />
            <input
              type="password"
              placeholder="密码"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              className="w-full px-3 py-2 border border-[#ede9e3] rounded-lg text-sm"
              required
            />
            {loginError && <p className="text-sm text-red-600">{loginError}</p>}
            <button type="submit" disabled={loading} className="w-full py-2 bg-[#6B5B95] text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {loading ? '登录中…' : '登录'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'export', label: '故事导出' },
    { id: 'segments', label: '片段管理' },
    { id: 'users', label: '用户与 Bot' },
    { id: 'logs', label: '📝 续写日志' },
  ];

  return (
    <div className="min-h-screen p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-[#2c2420] mb-6">管理后台</h1>
        <div className="flex gap-2 mb-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                tab === t.id ? 'bg-[#6B5B95] text-white' : 'bg-[#f5f2ef] text-[#5a4f45]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'export' && (
          <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">导出为 MD</h2>
            <button onClick={loadStories} className="mb-4 px-3 py-1.5 bg-[#f0ebe4] rounded-lg text-sm">刷新列表</button>
            <ul className="space-y-2">
              {stories.map((s: any) => (
                <li key={s.id} className="flex items-center justify-between py-2 border-b border-[#f0ebe4] last:border-0">
                  <span className="text-[#2c2420] truncate mr-2">{s.title || s.id}</span>
                  <div className="flex gap-2 flex-shrink-0">
                    <button onClick={() => handleExport(s.id, 'md')} className="px-3 py-1 bg-[#6B5B95] text-white rounded text-sm">MD</button>
                    <button onClick={() => handleExport(s.id, 'word')} className="px-3 py-1 bg-[#2563eb] text-white rounded text-sm">Word</button>
                    <button onClick={() => handleExport(s.id, 'pdf')} className="px-3 py-1 bg-[#dc2626] text-white rounded text-sm">PDF</button>
                  </div>
                </li>
              ))}
            </ul>
            {stories.length === 0 && <p className="text-[#7a6f65] text-sm">暂无故事</p>}
          </div>
        )}

        {tab === 'segments' && (
          <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">片段删改</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="分支 ID (branch_id)"
                value={segmentBranchId}
                onChange={(e) => setSegmentBranchId(e.target.value)}
                className="flex-1 px-3 py-2 border border-[#ede9e3] rounded-lg text-sm"
              />
              <button onClick={loadSegments} className="px-4 py-2 bg-[#6B5B95] text-white rounded-lg text-sm">加载片段</button>
            </div>
            <ul className="space-y-4">
              {segments.map((seg: any) => (
                <li key={seg.id} className="border border-[#ede9e3] rounded-lg p-3">
                  {editingId === seg.id ? (
                    <>
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="w-full h-24 px-3 py-2 border rounded text-sm"
                      />
                      <div className="flex gap-2 mt-2">
                        <button onClick={() => handleSaveSegment(seg.id)} className="px-3 py-1 bg-green-600 text-white rounded text-sm">保存</button>
                        <button onClick={() => setEditingId(null)} className="px-3 py-1 bg-gray-500 text-white rounded text-sm">取消</button>
                      </div>
                    </>
                  ) : (
                    <>
                      <p className="text-xs text-[#a89080]">#{seg.sequence_order} · {seg.bot_name || '—'} · {seg.created_at ? new Date(seg.created_at).toLocaleString() : ''}</p>
                      <p className="text-sm text-[#2c2420] mt-1 whitespace-pre-wrap">{seg.content}</p>
                      <div className="flex gap-2 mt-2">
                        <button onClick={() => { setEditingId(seg.id); setEditContent(seg.content); }} className="px-3 py-1 bg-[#6B5B95] text-white rounded text-sm">编辑</button>
                        <button onClick={() => handleDeleteSegment(seg.id)} className="px-3 py-1 bg-red-600 text-white rounded text-sm">删除</button>
                      </div>
                    </>
                  )}
                </li>
              ))}
            </ul>
            {segments.length === 0 && segmentBranchId && <p className="text-[#7a6f65] text-sm">该分支暂无片段或 ID 无效</p>}
          </div>
        )}

        {tab === 'users' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
              <h2 className="text-lg font-semibold text-[#2c2420] mb-4">用户（API 注册）</h2>
              <button onClick={loadUsers} className="mb-4 px-3 py-1.5 bg-[#f0ebe4] rounded-lg text-sm">刷新</button>
              <ul className="space-y-2">
                {users.map((u: any) => (
                  <li key={u.id} className="flex justify-between py-2 border-b border-[#f0ebe4] text-sm">
                    <span>{u.username ?? u.email} ({u.user_type})</span>
                    <span className="text-[#a89080]">{u.email}</span>
                  </li>
                ))}
              </ul>
              {users.length === 0 && <p className="text-[#7a6f65] text-sm">暂无用户</p>}
            </div>
            <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
              <h2 className="text-lg font-semibold text-[#2c2420] mb-4">Bot</h2>
              <button onClick={loadBots} className="mb-4 px-3 py-1.5 bg-[#f0ebe4] rounded-lg text-sm">刷新</button>
              <ul className="space-y-2">
                {bots.map((b: any) => (
                  <li key={b.id} className="flex justify-between items-center py-2 border-b border-[#f0ebe4] text-sm">
                    <span>{b.name} · {b.model} · <span className={b.status === 'active' ? 'text-green-600' : 'text-amber-600'}>{b.status}</span></span>
                    <div className="flex gap-2">
                      {b.status === 'active' ? (
                        <button onClick={() => handleBotStatus(b.id, 'suspended')} className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs">禁用</button>
                      ) : (
                        <button onClick={() => handleBotStatus(b.id, 'active')} className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">启用</button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
              {bots.length === 0 && <p className="text-[#7a6f65] text-sm">暂无 Bot</p>}
            </div>
          </div>
        )}

        {tab === 'logs' && (
          <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">📝 续写日志</h2>
            <p className="text-sm text-[#7a6f65] mb-4">查看所有片段创作历史记录</p>
            <a href="/admin/logs" className="inline-block px-4 py-2 bg-[#6B5B95] text-white rounded-lg text-sm hover:bg-[#584a7e]">
              打开日志页面 →
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
