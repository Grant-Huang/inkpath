// 统一 API 代理 - 支持子路径如 /api/proxy/dashboard/stats
// 与 proxy/route.ts 共用逻辑，此处处理 /api/proxy/xxx 的 catch-all

const PROXY_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://inkpath-api.onrender.com/api/v1';

async function proxyRequest(request: Request, pathSegments: string[] | undefined) {
  const pathStr = pathSegments?.length ? `/${pathSegments.join('/')}` : '';
  const url = new URL(request.url);
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return new Response(JSON.stringify({ error: '缺少认证 token' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const targetUrl = `${PROXY_BASE}${pathStr}${url.search}`;

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return new Response(
        JSON.stringify({
          error: data?.error?.message || `请求失败: ${response.status}`,
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
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

type RouteContext = { params: Promise<{ path?: string[] }> };

export async function GET(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function POST(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PUT(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PATCH(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function DELETE(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}
