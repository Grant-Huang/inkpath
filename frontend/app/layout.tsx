import type { Metadata } from 'next'
import { Playfair_Display, Inter } from 'next/font/google'
import './globals.css'
import { QueryClientProvider as QueryProvider } from './providers'
import TopNav from '../components/layout/TopNav'
import { Suspense } from 'react'

// Playfair Display 用于标题
const playfair = Playfair_Display({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-serif',
})

// Inter 用于正文
const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
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
      <body className={`${playfair.variable} ${inter.className} bg-[#faf8f5] text-[#2c2420]`}>
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
