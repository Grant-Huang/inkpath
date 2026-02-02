'use client';

import { useRouter, usePathname } from 'next/navigation';

interface TopNavProps {
  activeStoriesCount?: number;
}

export default function TopNav({ activeStoriesCount = 3 }: TopNavProps) {
  const router = useRouter();
  const pathname = usePathname();

  const isStoriesActive = pathname === '/stories' || pathname === '/';

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
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#6B5B95] flex items-center justify-center text-white text-[10px] sm:text-xs font-semibold">
          U
        </div>
      </div>
    </nav>
  );
}
