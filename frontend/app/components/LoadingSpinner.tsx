'use client';

import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  message?: string;
  className?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
  xl: 'h-16 w-16',
};

export default function LoadingSpinner({
  size = 'md',
  message,
  className = ''
}: LoadingSpinnerProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <Loader2 className={`${sizeClasses[size]} text-blue-500 animate-spin`} />
      {message && (
        <p className="text-slate-400 text-sm animate-pulse">{message}</p>
      )}
    </div>
  );
}

// Full page loading state
export function FullPageLoader({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-16 w-16 text-blue-500 animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-lg">{message}</p>
        <p className="text-slate-500 text-sm mt-2">Powered by Gemini 3</p>
      </div>
    </div>
  );
}

// Inline loading for buttons
export function ButtonLoader() {
  return <Loader2 className="h-4 w-4 animate-spin" />;
}
