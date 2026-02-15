'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** 已移除 AI 助手/写作页，重定向到首页 */
export default function WriterPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return null;
}
