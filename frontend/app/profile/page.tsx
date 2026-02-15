'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** 不提供普通作者个人中心界面，重定向到首页 */
export default function ProfilePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return null;
}
