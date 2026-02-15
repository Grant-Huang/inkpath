import { NextRequest, NextResponse } from 'next';

// 需要代理的 API 路径列表
const PROXY_PATHS = [
  '/admin/users',
  '/admin/bots',
  '/admin/users/',
  '/admin/bots/',
  '/admin/segments/',
  '/dashboard/stats',
];

export async function GET(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '');
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return NextResponse.json({ error: '缺少认证 token' }, { status: 401 });
  }

  // 检查是否需要代理
  const shouldProxy = PROXY_PATHS.some(p => path.startsWith(p));
  if (!shouldProxy) {
    return NextResponse.json({ error: '不需要代理' }, { status: 400 });
  }

  try {
    const response = await fetch(
      `https://inkpath-api.onrender.com/api/v1${path}${request.nextUrl.search}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return NextResponse.json(
        { error: data?.error?.message || `请求失败: ${response.status}` },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('代理错误:', error);
    return NextResponse.json({ error: '请求失败' }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '');
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return NextResponse.json({ error: '缺少认证 token' }, { status: 401 });
  }

  const shouldProxy = path.startsWith('/admin/bots/') || path.startsWith('/admin/segments/');
  if (!shouldProxy) {
    return NextResponse.json({ error: '不需要代理' }, { status: 400 });
  }

  try {
    const body = await request.json();
    
    const response = await fetch(
      `https://inkpath-api.onrender.com/api/v1${path}`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return NextResponse.json(
        { error: data?.error?.message || `请求失败: ${response.status}` },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('代理错误:', error);
    return NextResponse.json({ error: '请求失败' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '');
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return NextResponse.json({ error: '缺少认证 token' }, { status: 401 });
  }

  if (!path.startsWith('/admin/segments/')) {
    return NextResponse.json({ error: '不需要代理' }, { status: 400 });
  }

  try {
    const response = await fetch(
      `https://inkpath-api.onrender.com/api/v1${path}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return NextResponse.json(
        { error: data?.error?.message || `请求失败: ${response.status}` },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('代理错误:', error);
    return NextResponse.json({ error: '请求失败' }, { status: 500 });
  }
}
