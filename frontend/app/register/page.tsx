'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** 用户注册通过 API 进行，前端不提供注册页，重定向到首页 */
export default function RegisterPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return null;
}
