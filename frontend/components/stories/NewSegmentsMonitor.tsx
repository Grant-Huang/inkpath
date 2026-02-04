'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { segmentsApi } from '@/lib/api'

interface UseNewSegmentsMonitorProps {
  branchId: string | null
  initialSegments: any[]
  enabled?: boolean
  onNewSegments?: (newSegments: any[]) => void
}

export function useNewSegmentsMonitor({
  branchId,
  initialSegments,
  enabled = true,
  onNewSegments
}: UseNewSegmentsMonitorProps) {
  const [newSegmentsCount, setNewSegmentsCount] = useState(0)
  const [pendingSegments, setPendingSegments] = useState<any[]>([])
  const [isMonitoring, setIsMonitoring] = useState(false)
  const lastKnownCount = useRef(initialSegments.length)
  const lastKnownIds = useRef(new Set(initialSegments.map(s => s.id)))

  // 开始监测
  const startMonitoring = useCallback(() => {
    if (!branchId || !enabled) return
    setIsMonitoring(true)
  }, [branchId, enabled])

  // 停止监测
  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false)
    setNewSegmentsCount(0)
  }, [])

  // 加载新片段
  const loadNewSegments = useCallback(async () => {
    if (!branchId || pendingSegments.length === 0) return
    
    onNewSegments?.(pendingSegments)
    lastKnownIds.current = new Set([...lastKnownIds.current, ...pendingSegments.map(s => s.id)])
    lastKnownCount.current += pendingSegments.length
    setPendingSegments([])
    setNewSegmentsCount(0)
  }, [branchId, pendingSegments, onNewSegments])

  // 轮询检查新片段
  useEffect(() => {
    if (!isMonitoring || !branchId) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await segmentsApi.list(branchId)
        const segments = response.data?.segments || []
        const currentIds = new Set(segments.map((s: any) => s.id))
        
        // 找出新增的片段
        const newOnes: any[] = []
        segments.forEach((seg: any) => {
          if (!lastKnownIds.current.has(seg.id)) {
            newOnes.push(seg)
          }
        })

        if (newOnes.length > 0) {
          setPendingSegments(newOnes)
          setNewSegmentsCount(newOnes.length)
        }
      } catch (error) {
        console.error('监测新片段失败:', error)
      }
    }, 10000) // 每10秒检查一次

    return () => {
      clearInterval(pollInterval)
    }
  }, [isMonitoring, branchId])

  return {
    newSegmentsCount,
    pendingSegments,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    loadNewSegments
  }
}

// 悬浮的新片段计数器
export function NewSegmentsButton({ 
  count, 
  onClick, 
  onClose 
}: { 
  count: number
  onClick: () => void
  onClose: () => void
}) {
  if (count <= 0) return null

  return (
    <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50">
      <button
        onClick={onClick}
        className="flex items-center gap-2 bg-[#6B5B95] text-white px-4 py-2 rounded-full shadow-lg hover:bg-[#5a4a84] transition-colors animate-bounce"
      >
        <span className="text-lg">📥</span>
        <span className="font-medium">
          {count} 个新续写
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onClose()
          }}
          className="ml-1 text-white/70 hover:text-white"
        >
          ✕
        </button>
      </button>
    </div>
  )
}

// 移动端上拉追加组件
export function PullToAppend({ 
  hasMore, 
  loading, 
  onLoadMore 
}: { 
  hasMore: boolean
  loading: boolean
  onLoadMore: () => void
}) {
  const [isPulling, setIsPulling] = useState(false)
  const pullStartY = useRef<number>(0)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // 只在滚动到顶部时触发
    if (containerRef.current && containerRef.current.scrollTop > 50) return
    pullStartY.current = e.touches[0].clientY
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (pullStartY.current === 0 || !containerRef.current) return
    
    const currentY = e.touches[0].clientY
    const diff = currentY - pullStartY.current
    
    if (diff > 50) {
      setIsPulling(true)
    } else if (diff < 20) {
      setIsPulling(false)
    }
  }, [])

  const handleTouchEnd = useCallback(() => {
    if (isPulling) {
      onLoadMore()
    }
    setIsPulling(false)
    pullStartY.current = 0
  }, [isPulling, onLoadMore])

  if (!hasMore) return null

  return (
    <div
      ref={containerRef}
      className="w-full py-4 flex items-center justify-center"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {loading ? (
        <div className="flex items-center gap-2 text-[#a89080]">
          <div className="w-4 h-4 border-2 border-[#ede9e3] border-t-[#6B5B95] rounded-full animate-spin" />
          <span className="text-xs">加载中...</span>
        </div>
      ) : isPulling ? (
        <div className="flex items-center gap-2 text-[#6B5B95]">
          <span className="text-lg">⬆️</span>
          <span className="text-xs font-medium">释放加载更多</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-[#a89080]">
          <span className="text-lg">⬇️</span>
          <span className="text-xs">上拉加载新内容</span>
        </div>
      )}
    </div>
  )
}
