'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { storiesApi } from '@/lib/api';

export default function TopNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  
  // 获取活跃故事数
  const { data: storiesData } = useQuery({
    queryKey: ['stories-count'],
    queryFn: async () => {
      const response = await storiesApi.list();
      return response.data;
    },
    staleTime: 60 * 1000, // 1分钟缓存
    refetchInterval: 60 * 1000, // 每分钟刷新
  });
  
  // 计算活跃故事数（状态为active的故事）
  const activeStoriesCount = storiesData?.data?.stories?.filter(
    (story: any) => story.status === 'active'
  ).length || 0;

  const isStoriesActive = pathname === '/stories' || pathname === '/';
  const isLoginActive = pathname === '/login';
  const isRegisterActive = pathname === '/register';
  const isProfileActive = pathname === '/profile';

  // 检查登录状态
  useEffect(() => {
    const checkLoginStatus = () => {
      const token = localStorage.getItem('jwt_token');
      const userName = localStorage.getItem('user_name');
      const userEmail = localStorage.getItem('user_email');
      
      console.log('TopNav checking login status:', { token: !!token, userName, userEmail });
      
      if (token && userName) {
        setUser({ username: userName, email: userEmail });
      } else {
        setUser(null);
      }
    };
    
    // 初始检查
    checkLoginStatus();
    
    // 监听storage变化（其他标签页登录/退出）
    window.addEventListener('storage', checkLoginStatus);
    
    // 监听自定义登录事件
    window.addEventListener('login', checkLoginStatus);
    
    return () => {
      window.removeEventListener('storage', checkLoginStatus);
      window.removeEventListener('login', checkLoginStatus);
    };
  }, []);

  const handleLogout = () => {
    console.log('Logging out...');
    // 移除正确的key
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    setUser(null);
    router.push('/');
    router.refresh();
  };

  return (
    <nav className="sticky top-0 z-50 bg-[#faf8f5]/95 backdrop-blur-md border-b border-[#e8e4df] px-4 sm:px-6 md:px-10 h-14 flex items-center justify-between">
      <div className="flex items-center gap-2 sm:gap-4 md:gap-8">
        <div
          onClick={() => router.push('/')}
          className="flex items-center gap-1 sm:gap-2 cursor-pointer"
        >
          <span className="text-lg sm:text-xl tracking-tight serif font-bold text-[#2c2420]">
            墨径
          </span>
          <span className="text-[8px] sm:text-[10px] text-[#a89080] tracking-wider uppercase mt-0.5 hidden sm:inline">
            InkPath
          </span>
        </div>
        <div className="flex gap-0.5 sm:gap-1">
          <button
            onClick={() => router.push('/stories')}
            className={`px-2 sm:px-3.5 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-150 ${
              isStoriesActive
                ? 'bg-[#f0ebe4] text-[#2c2420]'
                : 'text-[#7a6f65] hover:bg-[#f0ebe4]'
            }`}
          >
            故事库
          </button>
        </div>
      </div>
      <div className="flex items-center gap-2 sm:gap-4">
        <span className="text-[10px] sm:text-xs text-[#a89080] hidden sm:inline">{activeStoriesCount} 个活跃故事</span>
        
        {user ? (
          // 已登录 - 显示用户菜单
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={() => router.push('/profile')}
              className={`flex items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-150 ${
                isProfileActive
                  ? 'bg-[#f0ebe4] text-[#2c2420]'
                  : 'text-[#7a6f65] hover:bg-[#f0ebe4]'
              }`}
            >
              <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-[#6B5B95] flex items-center justify-center text-white text-[9px] sm:text-xs font-semibold">
                {user.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="hidden sm:inline">{user.username || '用户'}</span>
            </button>
            <button
              onClick={handleLogout}
              className="text-[10px] sm:text-xs text-[#a89080] hover:text-[#E07A5F] transition-colors"
            >
              退出
            </button>
          </div>
        ) : (
          // 未登录 - 显示登录/注册按钮
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={() => router.push('/login')}
              className={`px-2 sm:px-3.5 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-150 ${
                isLoginActive
                  ? 'bg-[#f0ebe4] text-[#2c2420]'
                  : 'text-[#7a6f65] hover:bg-[#f0ebe4]'
              }`}
            >
              登录
            </button>
            <button
              onClick={() => router.push('/register')}
              className={`px-2 sm:px-3.5 py-1.5 rounded-md text-xs sm:text-sm font-medium bg-[#6B5B95] text-white hover:bg-[#5B4B85] transition-all duration-150 ${
                isRegisterActive ? 'bg-[#5B4B85]' : ''
              }`}
            >
              注册
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
