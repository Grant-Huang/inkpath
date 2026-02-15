// 统一 API 代理 - 解决 CORS 问题
// 支持的路径: /api/proxy/stories, /api/proxy/branches/*, /api/proxy/admin/*, /api/proxy/dashboard/*

const PROXY_BASE = 'https://inkpath-api.onrender.com/api/v1';

async function proxyRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname.replace('/api/proxy', '');
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');
  const search = url.search;

  if (!token) {
    return new Response(JSON.stringify({ error: '缺少认证 token' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const targetUrl = `${PROXY_BASE}${path}${search}`;
    
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return new Response(JSON.stringify({ error: data?.error?.message || `请求失败: ${response.status}` }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('代理错误:', error);
    return new Response(JSON.stringify({ error: '请求失败' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function GET(request) {
  return proxyRequest(request);
}

export async function POST(request) {
  return proxyRequest(request);
}

export async function PUT(request) {
  return proxyRequest(request);
}

export async function PATCH(request) {
  return proxyRequest(request);
}

export async function DELETE(request) {
  return proxyRequest(request);
}
