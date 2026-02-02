/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    // 前端运行在 5001，API 请求会被代理到 Flask
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
  // 性能优化配置
  compress: true, // 启用 Gzip 压缩
  poweredByHeader: false, // 移除 X-Powered-By 头
  // 配置反向代理：将 /api/* 请求转发到 Flask 后端
  // 注意：rewrites 不会影响 /_next/ 静态资源
  async rewrites() {
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:5002'
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
  // 优化图片和字体加载
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  // 实验性功能：优化编译
  experimental: {
    optimizeCss: true, // 优化 CSS
  },
}

module.exports = nextConfig
