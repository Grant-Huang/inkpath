'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    if (formData.password.length < 6) {
      setError('密码长度至少6位')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('https://inkpath-api.onrender.com/api/v1/auth/user/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          password: formData.password
        }),
      })

      const data = await response.json()

      if (data.status === 'success') {
        // 自动登录
        const loginResponse = await fetch('https://inkpath-api.onrender.com/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          }),
        })

        const loginData = await loginResponse.json()

        if (loginData.status === 'success') {
          localStorage.setItem('jwt_token', loginData.data.token)
          localStorage.setItem('user_name', loginData.data.user.name)
          localStorage.setItem('user_email', loginData.data.user.email)
          router.push('/')
          router.refresh()
        } else {
          // 注册成功但登录失败，跳转到登录页
          router.push('/login?registered=true')
        }
      } else {
        setError(data.error?.message || '注册失败')
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

        {/* 注册表单 */}
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-[#2c2420] mb-6 text-center">创建账号</h2>

          {error && (
            <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                用户名
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                placeholder="请输入用户名"
                required
              />
            </div>

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
                placeholder="至少6位密码"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#5a4f45] mb-1.5">
                确认密码
              </label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-4 py-2.5 focus:outline-none focus:border-[#6B5B95] focus:ring-1 focus:ring-[#6B5B95]"
                placeholder="再次输入密码"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#6B5B95] text-white py-2.5 rounded-lg font-medium hover:bg-[#5a4a85] transition-colors disabled:opacity-50"
            >
              {isLoading ? '注册中...' : '注册'}
            </button>
          </form>

          {/* 登录链接 */}
          <p className="text-center text-sm text-[#a89080] mt-4">
            已有账号？{' '}
            <a href="/login" className="text-[#6B5B95] hover:underline">
              立即登录
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
