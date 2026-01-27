'use client';

import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';
import StatusBadge, { type IncidentStatus } from './StatusBadge';
import { useAPI } from '@/lib/hooks/useAPI';
import { useToast } from './ErrorToast';

interface StatusChange {
  timestamp: string;
  from_status: IncidentStatus;
  to_status: IncidentStatus;
  updated_by: string;
  notes?: string;
}

interface StatusHistoryProps {
  incidentId: string;
}

export default function StatusHistory({ incidentId }: StatusHistoryProps) {
  const [history, setHistory] = useState<StatusChange[]>([]);
  const [loading, setLoading] = useState(true);
  const api = useAPI();
  const { showToast } = useToast();

  useEffect(() => {
    fetchStatusHistory();
  }, [incidentId]);

  const fetchStatusHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getStatusHistory(incidentId);
      // Map API response to our StatusChange type with proper typing
      const historyData: StatusChange[] = (data.history || []).map((item: any) => ({
        timestamp: item.timestamp,
        from_status: item.from_status as IncidentStatus,
        to_status: item.to_status as IncidentStatus,
        updated_by: item.updated_by,
        notes: item.notes,
      }));
      setHistory(historyData);
    } catch (error) {
      console.error('Error fetching status history:', error);
      // Don't show toast - this is not critical
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center p-8">
        <Clock className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400">No status changes yet</p>
        <p className="text-sm text-slate-500 mt-1">Status updates will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white mb-4">Status History</h3>
      
      <div className="relative space-y-6">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-px bg-slate-800"></div>

        {history.map((change, index) => (
          <div key={index} className="relative pl-12">
            {/* Timeline dot */}
            <div className="absolute left-0 top-1 w-8 h-8 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            </div>

            {/* Content */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  <StatusBadge status={change.from_status} size="sm" />
                  <span className="text-slate-500">→</span>
                  <StatusBadge status={change.to_status} size="sm" />
                </div>
                <span className="text-xs text-slate-500">
                  {formatTimestamp(change.timestamp)}
                </span>
              </div>

              {change.notes && (
                <p className="text-sm text-slate-400 mt-2">{change.notes}</p>
              )}

              <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                <span>Updated by:</span>
                <span className="font-medium text-slate-400">{change.updated_by}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}