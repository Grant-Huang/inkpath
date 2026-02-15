import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const storyId = searchParams.get('story_id');
  const format = searchParams.get('format') || 'md';
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!storyId) {
    return NextResponse.json({ error: '缺少 story_id' }, { status: 400 });
  }

  if (!token) {
    return NextResponse.json({ error: '缺少认证 token' }, { status: 401 });
  }

  try {
    const response = await fetch(
      `https://inkpath-api.onrender.com/api/v1/admin/stories/${storyId}/export?format=${format}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error?.error?.message || `导出失败: ${response.status}` },
        { status: response.status }
      );
    }

    const content = await response.text();
    
    // 获取文件名
    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = contentDisposition?.match(/filename="(.+)"/)?.[1] || `${storyId}.${format}`;

    return new NextResponse(content, {
      headers: {
        'Content-Type': format === 'md' ? 'text/markdown; charset=utf-8' : 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    });
  } catch (error) {
    console.error('导出代理错误:', error);
    return NextResponse.json({ error: '导出失败' }, { status: 500 });
  }
}
