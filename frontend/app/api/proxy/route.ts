// 统一 API 代理 - 解决 CORS 问题
// 公开 API（GET stories, branches, segments）无需认证
// 写入 API（POST/PUT/DELETE）需要认证

const PROXY_BASE = 'https://inkpath-api.onrender.com/api/v1';

// 公开 GET API 路径（无需认证）
const PUBLIC_GET_PATHS = [
  '/stories',
  '/branches/',
  '/segments',
  '/votes/summary',
];

function isPublicGet(path: string, method: string): boolean {
  if (method !== 'GET') return false;
  return PUBLIC_GET_PATHS.some(p => path.startsWith(p));
}

async function proxyRequest(request: Request) {
  const url = new URL(request.url);
  const path = url.pathname.replace('/api/proxy', '');
  const method = request.method;

  // 公开 GET API 无需认证
  if (!isPublicGet(path, method)) {
    const token = request.headers.get('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return new Response(JSON.stringify({ error: '缺少认证 token' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }

  try {
    const targetUrl = `${PROXY_BASE}${path}${url.search}`;
    
    const fetchOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // 写入操作需要认证
    if (!isPublicGet(path, method)) {
      const token = request.headers.get('Authorization')?.replace('Bearer ', '');
      fetchOptions.headers = {
        ...fetchOptions.headers,
        'Authorization': `Bearer ${token}`,
      };
    }

    // POST/PUT/PATCH 需要传递 body
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      fetchOptions.body = await request.text();
    }

    const response = await fetch(targetUrl, fetchOptions);

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

export async function GET(request: Request) {
  return proxyRequest(request);
}

export async function POST(request: Request) {
  return proxyRequest(request);
}

export async function PUT(request: Request) {
  return proxyRequest(request);
}

export async function PATCH(request: Request) {
  return proxyRequest(request);
}

export async function DELETE(request: Request) {
  return proxyRequest(request);
}
