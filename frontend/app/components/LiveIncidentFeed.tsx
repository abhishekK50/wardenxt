'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AlertCircle, Wifi, WifiOff, Clock, ChevronDown, ChevronUp, X } from 'lucide-react';
import { useAPI } from '@/lib/hooks/useAPI';

interface RecentIncident {
  incident_id: string;
  title: string;
  severity: string;
  status: string;
  created_at: string;
  source: string;
  auto_analyzed: boolean;
  services_affected: string[];
}

const severityColors: Record<string, string> = {
  P0: 'bg-red-500/20 text-red-400 border-red-500/50',
  P1: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
  P2: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  P3: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
};

const sourceIcons: Record<string, string> = {
  pagerduty: '📟',
  slack: '💬',
  generic: '🔔',
  manual: '👤',
};

export default function LiveIncidentFeed() {
  const [incidents, setIncidents] = useState<RecentIncident[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isHidden, setIsHidden] = useState(false);
  const api = useAPI();
  const router = useRouter();

  const fetchRecentIncidents = async () => {
    try {
      const response = await api.getRecentIncidents(5);

      if (!isConnected) {
        setIsConnected(true);
      }

      const newIncidents = response.incidents.slice(0, 3);
      setIncidents(newIncidents);

      if (isLoading) {
        setIsLoading(false);
      }
    } catch {
      setIsConnected(false);
      if (isLoading) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchRecentIncidents();
    const interval = setInterval(fetchRecentIncidents, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const handleIncidentClick = (incidentId: string) => {
    router.push(`/incidents/${incidentId}`);
  };

  // Hidden state - just show a small restore button
  if (isHidden) {
    return (
      <button
        onClick={() => setIsHidden(false)}
        className="fixed top-20 right-4 z-40 p-2 bg-slate-800/90 hover:bg-slate-700 border border-slate-700 rounded-lg shadow-lg transition-all"
        title="Show Live Feed"
      >
        <AlertCircle className="h-4 w-4 text-blue-400" />
      </button>
    );
  }

  // Collapsed state - minimal indicator
  if (!isExpanded) {
    return (
      <div className="fixed top-20 right-4 z-40">
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center gap-2 px-3 py-2 bg-slate-800/90 hover:bg-slate-700 border border-slate-700 rounded-lg shadow-lg transition-all group"
        >
          <div className="flex items-center gap-2">
            {isConnected ? (
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            ) : (
              <div className="h-2 w-2 rounded-full bg-red-500" />
            )}
            <span className="text-xs font-medium text-slate-300">Live Feed</span>
          </div>
          {incidents.length > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded">
              {incidents.length}
            </span>
          )}
          <ChevronDown className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
        </button>
      </div>
    );
  }

  // Expanded state
  return (
    <div className="fixed top-20 right-4 z-40 w-72 bg-slate-900/95 backdrop-blur-sm border border-slate-700 rounded-lg shadow-xl overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-blue-400" />
          <span className="text-xs font-semibold text-white">Live Feed</span>
          {isConnected ? (
            <Wifi className="h-3 w-3 text-green-500" />
          ) : (
            <WifiOff className="h-3 w-3 text-red-500" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(false)}
            className="p-1 hover:bg-slate-700 rounded transition-colors"
            title="Minimize"
          >
            <ChevronUp className="h-3 w-3 text-slate-400" />
          </button>
          <button
            onClick={() => setIsHidden(true)}
            className="p-1 hover:bg-slate-700 rounded transition-colors"
            title="Hide"
          >
            <X className="h-3 w-3 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Incidents List */}
      <div className="max-h-64 overflow-y-auto">
        {isLoading ? (
          <div className="p-3 text-center text-slate-500 text-xs">
            Loading...
          </div>
        ) : incidents.length === 0 ? (
          <div className="p-3 text-center text-slate-500 text-xs">
            No recent incidents
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {incidents.map((incident) => (
              <div
                key={incident.incident_id}
                onClick={() => handleIncidentClick(incident.incident_id)}
                className="p-2 hover:bg-slate-800/50 cursor-pointer transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span className="text-sm">{sourceIcons[incident.source] || '🔔'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${severityColors[incident.severity] || severityColors.P2}`}>
                        {incident.severity}
                      </span>
                      {incident.auto_analyzed && (
                        <span className="px-1 py-0.5 rounded text-[10px] bg-blue-500/20 text-blue-400">
                          AI
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-white font-medium truncate">
                      {incident.title}
                    </p>
                    <div className="flex items-center gap-1 text-[10px] text-slate-500 mt-0.5">
                      <Clock className="h-2.5 w-2.5" />
                      <span>{formatTimeAgo(incident.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {incidents.length > 0 && (
        <div className="px-3 py-1.5 bg-slate-800/50 border-t border-slate-800 text-center">
          <button
            onClick={() => router.push('/incidents')}
            className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
          >
            View all incidents →
          </button>
        </div>
      )}
    </div>
  );
}
