import { CheckCircle, AlertCircle, Search, Wrench, Eye, Clock, XCircle } from 'lucide-react';

export type IncidentStatus = 
  | 'DETECTED' 
  | 'INVESTIGATING' 
  | 'IDENTIFIED' 
  | 'MITIGATING' 
  | 'MONITORING' 
  | 'RESOLVED' 
  | 'CLOSED';

interface StatusBadgeProps {
  status: IncidentStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

const statusConfig = {
  DETECTED: {
    label: 'Detected',
    color: 'bg-red-500/10 text-red-400 border-red-500/30',
    icon: AlertCircle,
    glow: 'shadow-red-500/20',
  },
  INVESTIGATING: {
    label: 'Investigating',
    color: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    icon: Search,
    glow: 'shadow-orange-500/20',
  },
  IDENTIFIED: {
    label: 'Identified',
    color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    icon: CheckCircle,
    glow: 'shadow-yellow-500/20',
  },
  MITIGATING: {
    label: 'Mitigating',
    color: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    icon: Wrench,
    glow: 'shadow-blue-500/20',
  },
  MONITORING: {
    label: 'Monitoring',
    color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    icon: Eye,
    glow: 'shadow-cyan-500/20',
  },
  RESOLVED: {
    label: 'Resolved',
    color: 'bg-green-500/10 text-green-400 border-green-500/30',
    icon: CheckCircle,
    glow: 'shadow-green-500/20',
  },
  CLOSED: {
    label: 'Closed',
    color: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
    icon: XCircle,
    glow: 'shadow-slate-500/20',
  },
};

export default function StatusBadge({ status, size = 'md', showIcon = true }: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-2 rounded-full border font-semibold
        ${config.color}
        ${sizeClasses[size]}
        ${config.glow}
      `}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      {config.label}
    </span>
  );
}