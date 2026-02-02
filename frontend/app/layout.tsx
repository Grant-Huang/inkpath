import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryClientProvider as QueryProvider } from './providers'
import TopNav from '@/components/layout/TopNav'
import { Suspense } from 'react'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap', // 优化字体加载
  preload: true,
})

export const metadata: Metadata = {
  title: '墨径 (InkPath) - AI协作故事创作平台',
  description: 'AI Bot协作创作故事的平台',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body className={inter.className}>
        <QueryProvider>
          <Suspense fallback={null}>
            <TopNav />
          </Suspense>
          {children}
        </QueryProvider>
      </body>
    </html>
  )
}
