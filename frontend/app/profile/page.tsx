'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface UserInfo {
  id: string
  name: string
  email: string
  bio?: string
  avatar_url?: string
  created_at: string
}

export default function ProfilePage() {
  const router = useRouter()
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '',
    bio: ''
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // 获取用户信息
  useEffect(() => {
    const token = localStorage.getItem('jwt_token')
    if (!token) {
      router.push('/login')
      return
    }

    fetch('https://inkpath-api.onrender.com/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setUserInfo(data.data)
          setEditForm({
            name: data.data.name || '',
            bio: data.data.bio || ''
          })
        } else {
          // Token 过期
          localStorage.removeItem('jwt_token')
          router.push('/login')
        }
      })
      .catch(() => {
        localStorage.removeItem('jwt_token')
        router.push('/login')
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [router])

  // 保存个人信息
  const handleSave = async () => {
    setError('')
    setSuccess('')

    const token = localStorage.getItem('jwt_token')
    if (!token) return

    try {
      const response = await fetch('https://inkpath-api.onrender.com/api/v1/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(editForm)
      })

      const data = await response.json()

      if (data.status === 'success') {
        setUserInfo(data.data)
        setIsEditing(false)
        setSuccess('保存成功')
        // 更新本地存储的用户名
        localStorage.setItem('user_name', data.data.name)
      } else {
        setError(data.error?.message || '保存失败')
      }
    } catch (err) {
      setError('网络错误，请重试')
    }
  }

  // 退出登录
  const handleLogout = () => {
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('user_name')
    localStorage.removeItem('user_email')
    router.push('/')
    router.refresh()
  }

  // 格式化时间
  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#faf8f5] flex items-center justify-center">
        <div className="text-[#a89080]">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#faf8f5]">
      {/* 顶部导航 */}
      <div className="sticky top-0 bg-white border-b border-[#ede9e3] px-4 py-3 flex items-center justify-between z-10">
        <button onClick={() => router.back()} className="text-[#6B5B95]">
          ← 返回
        </button>
        <h1 className="text-lg font-semibold text-[#2c2420]">个人中心</h1>
        <div className="w-16"></div>
      </div>

      <div className="max-w-lg mx-auto p-4">
        {/* 成功/错误提示 */}
        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-50 text-green-600 text-sm p-3 rounded-lg mb-4">
            {success}
          </div>
        )}

        {/* 个人信息卡片 */}
        <div className="bg-white rounded-xl shadow p-6 mb-4">
          <div className="flex items-center gap-4 mb-6">
            {/* 头像 */}
            <div className="w-16 h-16 rounded-full bg-[#6B5B95] text-white flex items-center justify-center text-2xl font-semibold">
              {userInfo?.name?.charAt(0) || '?'}
            </div>
            
            {/* 基本信息 */}
            <div className="flex-1">
              {isEditing ? (
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full border border-[#ede9e3] rounded px-3 py-1.5 text-lg font-semibold text-[#2c2420]"
                  placeholder="用户名"
                />
              ) : (
                <h2 className="text-xl font-semibold text-[#2c2420]">
                  {userInfo?.name || '未设置'}
                </h2>
              )}
              <p className="text-sm text-[#a89080]">{userInfo?.email}</p>
            </div>
          </div>

          {/* 个人简介 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-[#5a4f45] mb-2">
              个人简介
            </label>
            {isEditing ? (
              <textarea
                value={editForm.bio}
                onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                className="w-full border border-[#ede9e3] rounded-lg px-4 py-2 text-sm text-[#5a4f45] resize-none focus:outline-none focus:border-[#6B5B95]"
                rows={3}
                placeholder="介绍一下自己..."
              />
            ) : (
              <p className="text-sm text-[#5a4f45]">
                {userInfo?.bio || '暂无简介'}
              </p>
            )}
          </div>

          {/* 注册时间 */}
          <div className="text-xs text-[#a89080] mb-4">
            注册于 {userInfo?.created_at ? formatDate(userInfo.created_at) : '未知'}
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={handleSave}
                  className="flex-1 bg-[#6B5B95] text-white py-2 rounded-lg text-sm font-medium hover:bg-[#5a4a85]"
                >
                  保存
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false)
                    setEditForm({
                      name: userInfo?.name || '',
                      bio: userInfo?.bio || ''
                    })
                  }}
                  className="flex-1 border border-[#ede9e3] text-[#5a4f45] py-2 rounded-lg text-sm font-medium hover:bg-[#faf8f5]"
                >
                  取消
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="flex-1 bg-[#6B5B95] text-white py-2 rounded-lg text-sm font-medium hover:bg-[#5a4a85]"
              >
                编辑资料
              </button>
            )}
          </div>
        </div>

        {/* 其他操作 */}
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold text-[#2c2420] mb-4">账户安全</h3>
          
          <div className="space-y-3">
            <button
              onClick={handleLogout}
              className="w-full border border-red-200 text-red-600 py-2 rounded-lg text-sm font-medium hover:bg-red-50"
            >
              退出登录
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
