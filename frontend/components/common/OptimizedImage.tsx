/**
 * 优化的图片组件
 * 使用 Next.js Image 组件提供自动优化
 */
import Image from 'next/image'
import { useState } from 'react'

interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  priority?: boolean
  placeholder?: 'blur' | 'empty'
  blurDataURL?: string
}

export default function OptimizedImage({
  src,
  alt,
  width,
  height,
  className = '',
  priority = false,
  placeholder = 'empty',
  blurDataURL,
}: OptimizedImageProps) {
  const [error, setError] = useState(false)

  if (error) {
    // 图片加载失败时的占位符
    return (
      <div
        className={`bg-gray-200 flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        <span className="text-gray-400 text-sm">图片加载失败</span>
      </div>
    )
  }

  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      className={className}
      priority={priority}
      placeholder={placeholder}
      blurDataURL={blurDataURL}
      onError={() => setError(true)}
      // 优化配置
      loading={priority ? undefined : 'lazy'}
      quality={85}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  )
}
