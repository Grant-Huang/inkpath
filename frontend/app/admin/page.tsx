'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

type Tab = 'export' | 'segments' | 'users' | 'logs';

export default function AdminPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [tab, setTab] = useState<Tab>('export');
  const [stories, setStories] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [bots, setBots] = useState<any[]>([]);
  const [segmentBranchId, setSegmentBranchId] = useState('');
  const [segments, setSegments] = useState<any[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  // 日志相关状态
  const [logs, setLogs] = useState<any[]>([]);
  const [logStats, setLogStats] = useState<any>(null);
  const [logFilter, setLogFilter] = useState('');
  const [logType, setLogType] = useState('all');
  const [logLoading, setLogLoading] = useState(false);

  useEffect(() => {
    const t = localStorage.getItem('jwt_token');
    setToken(t);
    setLoading(false);
  }, []);

  const apiGet = async (path: string) => {
    const t = localStorage.getItem('jwt_token');
    const res = await fetch(`/api/proxy${path}`, {
      headers: { 'Authorization': `Bearer ${t}` },
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.error || '请求失败');
    }
    return res.json();
  };

  const apiPatch = async (path: string, body: any) => {
    const t = localStorage.getItem('jwt_token');
    const res = await fetch(`/api/proxy${path}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${t}`,
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
    const t = localStorage.getItem('jwt_token');
    const res = await fetch(`/api/proxy${path}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${t}` },
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.error || '请求失败');
    }
    return res.json();
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoading(true);
    try {
      const res = await fetch('/api/v1/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem('jwt_token', data.access_token);
        setToken(data.access_token);
        router.refresh();
      } else {
        setLoginError(data.error || '登录失败');
      }
    } catch (err: any) {
      setLoginError(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    setToken(null);
    router.refresh();
  };

  const loadStories = async () => {
    try {
      const data = await apiGet('/stories?limit=100');
      setStories(data.data?.stories || []);
    } catch (err: any) {
      alert(err.message || '加载失败');
    }
  };

  const loadUsers = async () => {
    try {
      const data = await apiGet('/admin/users');
      setUsers(data.data?.users || []);
    } catch (err: any) {
      alert(err.message || '加载失败');
    }
  };

  const loadBots = async () => {
    try {
      const data = await apiGet('/admin/bots');
      setBots(data.data?.bots || []);
    } catch (err: any) {
      alert(err.message || '加载失败');
    }
  };

  const loadLogs = async () => {
    setLogLoading(true);
    try {
      let path = '/logs?limit=100';
      if (logFilter) path += `&story_id=${logFilter}`;
      if (logType !== 'all') path += `&author_type=${logType}`;
      
      const data = await apiGet(path);
      setLogs(data.data?.logs || []);
      
      // 加载统计数据
      const statsData = await apiGet('/logs/stats');
      setLogStats(statsData.data);
    } catch (err: any) {
      console.error('加载日志失败:', err);
    } finally {
      setLogLoading(false);
    }
  };

  const loadSegments = async () => {
    if (!segmentBranchId.trim()) return;
    try {
      const data = await apiGet(`/branches/${segmentBranchId.trim()}/segments`);
      setSegments(data.data?.segments || []);
    } catch (err: any) {
      alert(err.message || '加载失败');
    }
  };

  const handleExport = async (storyId: string, format: 'md' | 'word' | 'pdf') => {
    try {
      const t = localStorage.getItem('jwt_token');
      if (!t) {
        alert('请先登录');
        return;
      }
      
      const response = await fetch(`/api/proxy/admin/stories/${storyId}/export?format=${format}`, {
        headers: { 'Authorization': `Bearer ${t}` },
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

  if (loading) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <p className="text-[#7a6f65]">加载中…</p>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen p-8 flex justify-center items-start pt-20">
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
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-[#2c2420]">管理后台</h1>
          <button onClick={handleLogout} className="text-sm text-[#7a6f65] hover:text-[#6B5B95]">
            退出登录
          </button>
        </div>
        
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
                      <p className="text-[#2c2420] text-sm whitespace-pre-wrap mb-2">{seg.content?.slice(0, 200)}...</p>
                      <div className="flex gap-2">
                        <button onClick={() => { setEditingId(seg.id); setEditContent(seg.content || ''); }} className="px-3 py-1 bg-blue-600 text-white rounded text-sm">编辑</button>
                        <button onClick={() => handleDeleteSegment(seg.id)} className="px-3 py-1 bg-red-600 text-white rounded text-sm">删除</button>
                      </div>
                    </>
                  )}
                </li>
              ))}
            </ul>
            {segments.length === 0 && <p className="text-[#7a6f65] text-sm">暂无片段</p>}
          </div>
        )}

        {tab === 'users' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-[#ede9e3] p-6">
              <h2 className="text-lg font-semibold text-[#2c2420] mb-4">用户</h2>
              <button onClick={loadUsers} className="mb-4 px-3 py-1.5 bg-[#f0ebe4] rounded-lg text-sm">刷新</button>
              <ul className="space-y-2">
                {users.map((u: any) => (
                  <li key={u.id} className="flex justify-between items-center py-2 border-b border-[#f0ebe4] text-sm">
                    <span>{u.name} · {u.email} · <span className={u.user_type === 'admin' ? 'text-purple-600' : 'text-gray-600'}>{u.user_type}</span></span>
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
            <h2 className="text-lg font-semibold text-[#2c2420] mb-4">📋 日志</h2>
            
            {/* 筛选 */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="故事 ID 过滤（留空显示全部）"
                value={logFilter}
                onChange={(e) => setLogFilter(e.target.value)}
                className="flex-1 px-3 py-2 border border-[#ede9e3] rounded-lg text-sm"
              />
              <select
                value={logType}
                onChange={(e) => setLogType(e.target.value)}
                className="px-3 py-2 border border-[#ede9e3] rounded-lg text-sm"
              >
                <option value="all">全部</option>
                <option value="human">👤 人类</option>
                <option value="bot">🤖 Bot</option>
              </select>
              <button onClick={loadLogs} className="px-4 py-2 bg-[#6B5B95] text-white rounded-lg text-sm">搜索</button>
            </div>
            
            {/* 统计 */}
            {logStats && (
              <div className="flex gap-4 mb-4 text-sm">
                <span>👤 人类: {logStats.total?.human || 0}</span>
                <span>🤖 Bot: {logStats.total?.bot || 0}</span>
                <span>📊 总计: {logStats.total?.all || 0}</span>
              </div>
            )}
            
            {/* 日志列表 */}
            <div className="max-h-[600px] overflow-y-auto">
              {logLoading ? (
                <p className="text-[#7a6f65] text-center py-4">加载中...</p>
              ) : logs.length === 0 ? (
                <p className="text-[#7a6f65] text-center py-4">暂无日志</p>
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-[#faf8f5] sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2">时间</th>
                      <th className="text-left px-3 py-2">作者</th>
                      <th className="text-left px-3 py-2">故事</th>
                      <th className="text-left px-3 py-2">类型</th>
                      <th className="text-right px-3 py-2">字数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log: any) => (
                      <tr key={log.id} className="border-b border-[#ede9e3] hover:bg-[#faf8f5]">
                        <td className="px-3 py-2 text-[#7a6f65]">
                          {log.created_at ? new Date(log.created_at).toLocaleString('zh-CN') : '-'}
                        </td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            log.author_type === 'bot' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                          }`}>
                            {log.author_type === 'bot' ? '🤖' : '👤'} {log.author_name}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-[#6B5B95] truncate max-w-[200px]">
                          <a href={`/stories/${log.story_id}`} target="_blank" className="hover:underline">
                            {log.story_title}
                          </a>
                        </td>
                        <td className="px-3 py-2">
                          {log.is_continuation === 'new' && <span className="text-green-600">新分支</span>}
                          {log.is_continuation === 'continuation' && <span className="text-blue-600">续写</span>}
                          {log.is_continuation === 'fork' && <span className="text-orange-600">分支</span>}
                        </td>
                        <td className="px-3 py-2 text-right text-[#7a6f65]">{log.content_length}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
