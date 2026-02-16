// 测试端点
export async function GET() {
  return new Response(JSON.stringify({ 
    message: 'Proxy API is working',
    timestamp: new Date().toISOString()
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
