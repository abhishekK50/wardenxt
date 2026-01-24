'use client';

import { useEffect, useState } from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

export type ToastType = 'error' | 'success' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ErrorToastProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const toastConfig = {
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-500/10 border-red-500/30',
    iconColor: 'text-red-400',
    textColor: 'text-red-200',
  },
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-500/10 border-green-500/30',
    iconColor: 'text-green-400',
    textColor: 'text-green-200',
  },
  info: {
    icon: Info,
    bgColor: 'bg-blue-500/10 border-blue-500/30',
    iconColor: 'text-blue-400',
    textColor: 'text-blue-200',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-yellow-500/10 border-yellow-500/30',
    iconColor: 'text-yellow-400',
    textColor: 'text-yellow-200',
  },
};

export function ErrorToast({ toast, onDismiss }: ErrorToastProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const duration = toast.duration || 5000;
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => onDismiss(toast.id), 300); // Wait for fade out
    }, duration);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onDismiss]);

  const config = toastConfig[toast.type];
  const Icon = config.icon;

  return (
    <div
      className={`
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}
        transition-all duration-300
        ${config.bgColor} border rounded-lg p-4 shadow-lg
        flex items-start gap-3 min-w-[300px] max-w-md
      `}
    >
      <Icon className={`h-5 w-5 ${config.iconColor} flex-shrink-0 mt-0.5`} />
      <p className={`flex-1 ${config.textColor} text-sm`}>{toast.message}</p>
      <button
        onClick={() => {
          setIsVisible(false);
          setTimeout(() => onDismiss(toast.id), 300);
        }}
        className="text-slate-400 hover:text-slate-200 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (message: string, type: ToastType = 'error', duration?: number) => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, message, type, duration }]);
    return id;
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const ToastContainer = () => (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <ErrorToast key={toast.id} toast={toast} onDismiss={dismissToast} />
      ))}
    </div>
  );

  return {
    showToast,
    dismissToast,
    ToastContainer,
  };
}
