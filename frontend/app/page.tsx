'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    router.push('/incidents');
  }, [router]);
  
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-white">Redirecting to incidents...</div>
    </div>
  );
}