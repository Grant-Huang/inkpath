/**
 * 骨架屏组件 - 匹配demo设计规范
 */
export function StoryListSkeleton() {
  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <div className="mb-10">
        <div className="h-9 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
        <div className="h-5 bg-gray-200 rounded w-64 animate-pulse"></div>
      </div>
      <div className="space-y-0.5">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-[#ede9e3] rounded-lg p-6 animate-pulse">
            <div className="flex justify-between items-start">
              <div className="flex-1 max-w-[520px]">
                <div className="flex items-center gap-2.5 mb-1.5">
                  <div className="h-5 bg-gray-200 rounded-full w-12"></div>
                  <div className="h-4 bg-gray-200 rounded w-16"></div>
                </div>
                <div className="h-7 bg-gray-200 rounded w-48 mb-1"></div>
                <div className="h-5 bg-gray-200 rounded w-full mb-2.5"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              </div>
              <div className="flex flex-col items-end gap-2 ml-6">
                <div className="h-4 bg-gray-200 rounded w-16"></div>
                <div className="h-4 bg-gray-200 rounded w-12 mt-0.5"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function StoryDetailSkeleton() {
  return (
    <div className="max-w-[1080px] mx-auto px-4 sm:px-6 py-8 animate-pulse">
      <div className="mb-7 hidden lg:block">
        <div className="flex items-center gap-2.5 mb-1">
          <div className="h-5 bg-gray-200 rounded-full w-12"></div>
          <div className="h-4 bg-gray-200 rounded w-32"></div>
        </div>
        <div className="h-8 bg-gray-200 rounded w-64 mb-1"></div>
        <div className="h-5 bg-gray-200 rounded w-96"></div>
      </div>
      <div className="space-y-6">
        <div className="h-6 bg-gray-200 rounded w-full"></div>
        <div className="h-6 bg-gray-200 rounded w-full"></div>
        <div className="h-6 bg-gray-200 rounded w-3/4"></div>
      </div>
    </div>
  )
}

export function SegmentCardSkeleton() {
  return (
    <div className="relative flex gap-4 pb-6">
      <div className="w-7.5 h-7.5 rounded-full bg-gray-200 flex-shrink-0 z-10 animate-pulse"></div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <div className="h-5 bg-gray-200 rounded w-16"></div>
          <div className="h-4 bg-gray-200 rounded w-20"></div>
        </div>
        <div className="space-y-2 mb-2.5">
          <div className="h-5 bg-gray-200 rounded w-full"></div>
          <div className="h-5 bg-gray-200 rounded w-full"></div>
          <div className="h-5 bg-gray-200 rounded w-5/6"></div>
        </div>
        <div className="flex gap-4">
          <div className="h-8 bg-gray-200 rounded w-16"></div>
          <div className="h-8 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
    </div>
  )
}
