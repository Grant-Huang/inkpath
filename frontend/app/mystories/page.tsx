'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** 已移除「我的故事」页，重定向到首页 */
export default function MystoriesPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return null;
}
