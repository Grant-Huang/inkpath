'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch('https://inkpath-api.onrender.com/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (data.status === 'success') {
        // 保存 token
        localStorage.setItem('jwt_token', data.data.token)
        localStorage.setItem('user_name', data.data.user.name)
        localStorage.setItem('user_email', data.data.user.email)
        
        // 跳转到首页
        router.push('/')
        router.refresh()
      } else {
        setError(data.error?.message || '登录失败')
      }
    } catch (err) {
      setError('网络错误，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#faf8f5] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl serif font-bold text-[#2c2420]">墨径</h1>
          <p className="text-[#a89080] mt-1">InkPath</p>
        </div>

        {/* 登录表单 */}
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-[#2c2420] mb-6 text-center">登录账号</h2>

          {error && (
            <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                邮箱
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                placeholder="请输入邮箱"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                密码
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                placeholder="请输入密码"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#6B5B95] text-white py-2.5 rounded-lg font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50"
            >
              {isLoading ? '登录中...' : '登录'}
            </button>
          </form>

          {/* 注册链接 */}
          <p className="text-center text-sm text-[#a89080] mt-4">
            还没有账号？{' '}
            <a href="/register" className="text-[#6B5B95] hover:underline">
              立即注册
            </a>
          </p>
        </div>

        {/* 返回首页 */}
        <p className="text-center text-sm text-[#a89080] mt-4">
          <a href="/" className="hover:text-[#6B5B95]">
            ← 返回首页
          </a>
        </p>
      </div>
    </div>
  )
}
