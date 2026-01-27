'use client';

import { useState } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import type { IncidentStatus } from './StatusBadge';
import { useAPI } from '@/lib/hooks/useAPI';
import { useToast } from './ErrorToast';

interface StatusUpdateDropdownProps {
  incidentId: string;
  currentStatus: IncidentStatus;
  onStatusChange: (newStatus: IncidentStatus) => void;
}

const allStatuses: IncidentStatus[] = [
  'DETECTED',
  'INVESTIGATING',
  'IDENTIFIED',
  'MITIGATING',
  'MONITORING',
  'RESOLVED',
  'CLOSED',
];

const statusLabels: Record<IncidentStatus, string> = {
  DETECTED: 'Detected',
  INVESTIGATING: 'Investigating',
  IDENTIFIED: 'Identified',
  MITIGATING: 'Mitigating',
  MONITORING: 'Monitoring',
  RESOLVED: 'Resolved',
  CLOSED: 'Closed',
};

export default function StatusUpdateDropdown({
  incidentId,
  currentStatus,
  onStatusChange,
}: StatusUpdateDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const api = useAPI();
  const { showToast } = useToast();

  const handleStatusChange = async (newStatus: IncidentStatus) => {
    if (newStatus === currentStatus) {
      setIsOpen(false);
      return;
    }

    setIsUpdating(true);
    
    try {
      await api.updateIncidentStatus(incidentId, {
        new_status: newStatus,
        updated_by: 'User',
        notes: `Status changed from ${currentStatus} to ${newStatus}`,
      });

      onStatusChange(newStatus);
      setIsOpen(false);
      showToast(`Status updated to ${statusLabels[newStatus]}`, 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update status';
      console.error('Error updating status:', error);
      showToast(errorMessage, 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isUpdating}
        className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700 disabled:opacity-50"
      >
        <span className="text-sm font-medium">
          {isUpdating ? 'Updating...' : 'Update Status'}
        </span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-800 rounded-lg shadow-xl z-20 overflow-hidden">
            <div className="p-2 border-b border-slate-800">
              <p className="text-xs text-slate-400 font-medium px-2 py-1">
                Change Status
              </p>
            </div>
            <div className="p-2 max-h-64 overflow-y-auto">
              {allStatuses.map((status) => (
                <button
                  key={status}
                  onClick={() => handleStatusChange(status)}
                  disabled={isUpdating}
                  className={`
                    w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors
                    ${status === currentStatus
                      ? 'bg-blue-500/10 text-blue-400'
                      : 'text-slate-300 hover:bg-slate-800'
                    }
                    disabled:opacity-50
                  `}
                >
                  <span>{statusLabels[status]}</span>
                  {status === currentStatus && (
                    <Check className="h-4 w-4" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}