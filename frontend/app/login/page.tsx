'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** 用户登录通过 API 进行，前端不提供登录页，重定向到首页 */
export default function LoginPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return null;
}
