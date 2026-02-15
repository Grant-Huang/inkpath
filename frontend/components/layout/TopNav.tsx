'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { storiesApi } from '@/lib/api';

/** 顶部导航：用户登录通过 API，不展示登录/注册/个人中心；已移除 AI 助手 */
export default function TopNav() {
  const router = useRouter();
  const pathname = usePathname();

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
  const isAgentActive = pathname.startsWith('/agent');
  const isDashboardActive = pathname.startsWith('/dashboard');
  const isAdminActive = pathname.startsWith('/admin');

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
          <button
            onClick={() => router.push('/agent')}
            className={`px-2 sm:px-3.5 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-150 ${
              isAgentActive
                ? 'bg-[#6B5B95] text-white'
                : 'text-[#7a6f65] hover:bg-[#f0ebe4]'
            }`}
          >
            Agent
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className={`px-2 sm:px-3.5 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-150 ${
              isDashboardActive
                ? 'bg-[#f0ebe4] text-[#2c2420]'
                : 'text-[#7a6f65] hover:bg-[#f0ebe4]'
            }`}
          >
            数据
          </button>
          <button
            onClick={() => router.push('/admin')}
            className={`px-2 sm:px-3.5 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-150 ${
              isAdminActive
                ? 'bg-[#f0ebe4] text-[#2c2420]'
                : 'text-[#7a6f65] hover:bg-[#f0ebe4]'
            }`}
          >
            管理
          </button>
        </div>
      </div>
      <div className="flex items-center gap-2 sm:gap-4">
        <span className="text-[10px] sm:text-xs text-[#a89080] hidden sm:inline">{activeStoriesCount} 个活跃故事</span>
      </div>
    </nav>
  );
}
