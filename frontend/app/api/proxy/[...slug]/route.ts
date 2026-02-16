// 统一 API 代理 - 解决 CORS 问题
// 公开 GET API（stories, branches, segments）无需认证
// 写入 API 需要认证

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

async function proxyRequest(request: Request, slug: string[] | undefined) {
  const segments = Array.isArray(slug) ? slug : [];
  const path = segments.length > 0 ? '/' + segments.join('/') : '';
  const method = request.method;
  const url = new URL(request.url);
  const query = url.search || '';
  if (!path) {
    return new Response(JSON.stringify({ error: '代理路径不能为空' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // 公开 GET API 无需认证
  let authRequired = !isPublicGet(path, method);
  let token = '';
  
  if (authRequired) {
    token = request.headers.get('Authorization')?.replace('Bearer ', '') || '';
    if (!token) {
      return new Response(JSON.stringify({ error: '缺少认证 token' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }

  try {
    const targetUrl = `${PROXY_BASE}${path}${query}`;
    
    const fetchOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (authRequired) {
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

    // 尝试获取 Content-Type
    const contentType = response.headers.get('Content-Type') || '';
    
    // 如果是 JSON 响应，解析并返回
    if (contentType.includes('application/json')) {
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
    }

    // 非 JSON 响应（文件导出等），直接透传
    if (!response.ok) {
      const text = await response.text();
      return new Response(JSON.stringify({ error: text || `请求失败: ${response.status}` }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 获取响应头（透传关键头）
    const newHeaders = new Headers();
    response.headers.forEach((value, key) => {
      if (['content-type', 'content-disposition', 'content-length'].includes(key.toLowerCase())) {
        newHeaders.set(key, value);
      }
    });

    const blob = await response.blob();
    return new Response(blob, {
      status: response.status,
      headers: newHeaders,
    });
  } catch (error) {
    console.error('代理错误:', error);
    return new Response(JSON.stringify({ error: '请求失败' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function GET(request: Request, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  return proxyRequest(request, slug);
}

export async function POST(request: Request, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  return proxyRequest(request, slug);
}

export async function PUT(request: Request, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  return proxyRequest(request, slug);
}

export async function PATCH(request: Request, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  return proxyRequest(request, slug);
}

export async function DELETE(request: Request, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  return proxyRequest(request, slug);
}
