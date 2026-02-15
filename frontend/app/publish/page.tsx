'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** 已移除发布页，重定向到首页 */
export default function PublishPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return null;
}
