// 统一 API 代理 - 解决 CORS 问题

const PROXY_PATHS = [
  '/admin/users',
  '/admin/bots',
  '/admin/users/',
  '/admin/bots/',
  '/admin/segments/',
  '/dashboard/stats',
];

async function handleRequest(request) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '');
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return new Response(JSON.stringify({ error: '缺少认证 token' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const shouldProxy = PROXY_PATHS.some((p) => path.startsWith(p));
  if (!shouldProxy) {
    return new Response(JSON.stringify({ error: '不需要代理' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const url = `https://inkpath-api.onrender.com/api/v1${path}${request.nextUrl.search}`;
    
    const response = await fetch(url, {
      method: request.method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: request.body ? JSON.stringify(await request.json()) : undefined,
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
  return handleRequest(request);
}

export async function POST(request) {
  return handleRequest(request);
}

export async function PUT(request) {
  return handleRequest(request);
}

export async function PATCH(request) {
  return handleRequest(request);
}

export async function DELETE(request) {
  return handleRequest(request);
}
