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
  // 生产环境移除console
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // 配置反向代理：将 /api/* 请求转发到 Flask 后端
  // 注意：rewrites 不会影响 /_next/ 静态资源
  async rewrites() {
    // 优先使用 BACKEND_API_URL，如果没有则使用 NEXT_PUBLIC_API_URL，最后使用默认值
    const backendUrl = process.env.BACKEND_API_URL || 
                      process.env.NEXT_PUBLIC_API_URL || 
                      'http://localhost:5002'
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
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  // 实验性功能：优化编译
  experimental: {
    // optimizeCss: true, // 暂时禁用，需要critters依赖
    optimizePackageImports: ['@tanstack/react-query', 'axios'],
  },
  // 确保路径别名生效
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': require('path').resolve(__dirname, '.'),
    }
    return config
  },
}

module.exports = nextConfig
