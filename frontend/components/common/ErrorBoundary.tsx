/**
 * 错误边界组件
 * 捕获子组件错误，显示友好的错误页面
 */
'use client'

import { Component, ErrorInfo, ReactNode } from 'react'
import Link from 'next/link'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: string | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error,
      errorInfo: errorInfo.componentStack || null,
    })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 检查是否是404错误
      const is404 = this.state.error?.message?.includes('404') || 
                    this.state.error?.message?.includes('not found')

      return (
        <div className="min-h-screen flex items-center justify-center bg-[#faf8f5]">
          <div className="max-w-md w-full mx-4 text-center">
            <div className="mb-8">
              <span className="text-6xl font-serif text-[#6B5B95]">
                {is404 ? '404' : '出错啦'}
              </span>
            </div>
            
            <h1 className="text-2xl font-serif text-[#2c2420] mb-4">
              {is404 ? '页面不存在' : '出了点问题'}
            </h1>
            
            <p className="text-[#7a6f65] mb-8">
              {is404 
                ? '您访问的页面不存在或已被删除'
                : '加载过程中发生了错误，请稍后重试'}
            </p>

            <div className="space-y-4">
              <button
                onClick={() => window.location.reload()}
                className="block w-full py-3 px-6 bg-[#6B5B95] text-white rounded-lg hover:bg-[#5a4a84] transition-colors"
              >
                刷新页面
              </button>
              
              <Link
                href="/"
                className="block w-full py-3 px-6 border border-[#d9d3ca] text-[#2c2420] rounded-lg hover:bg-[#f5f2ed] transition-colors"
              >
                返回首页
              </Link>
            </div>

            {/* 开发环境显示详细错误 */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-8 text-left text-sm text-[#a89080]">
                <summary className="cursor-pointer">查看错误详情</summary>
                <pre className="mt-2 p-4 bg-[#f5f2ed] rounded overflow-auto">
                  {this.state.error?.toString()}
                  {this.state.errorInfo && `\n\n${this.state.errorInfo}`}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
