'use client';

import { Cpu, HardDrive, Network, AlertCircle, X, Zap, TrendingUp, Activity } from 'lucide-react';
import { Anomaly } from '@/lib/api';

interface AnomalyAlertProps {
  anomaly: Anomaly;
  onDismiss?: (anomalyId: string) => void;
  onInvestigate?: (anomaly: Anomaly) => void;
  onCreateIncident?: (anomaly: Anomaly) => void;
}

export default function AnomalyAlert({
  anomaly,
  onDismiss,
  onInvestigate,
  onCreateIncident
}: AnomalyAlertProps) {
  const getMetricIcon = (metricType: string) => {
    switch (metricType) {
      case 'cpu':
        return <Cpu className="h-5 w-5" />;
      case 'memory':
        return <HardDrive className="h-5 w-5" />;
      case 'network':
        return <Network className="h-5 w-5" />;
      case 'latency':
        return <Activity className="h-5 w-5" />;
      case 'error':
        return <AlertCircle className="h-5 w-5" />;
      default:
        return <Zap className="h-5 w-5" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'severe':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          icon: 'text-red-400',
          badge: 'bg-red-500/20 text-red-400 border-red-500/30'
        };
      case 'moderate':
        return {
          bg: 'bg-orange-500/10',
          border: 'border-orange-500/30',
          icon: 'text-orange-400',
          badge: 'bg-orange-500/20 text-orange-400 border-orange-500/30'
        };
      default: // minor
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          icon: 'text-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
        };
    }
  };

  const colors = getSeverityColor(anomaly.severity);
  const formatValue = (value: number, metricName: string) => {
    if (metricName.includes('percent') || metricName.includes('rate')) {
      return `${value.toFixed(1)}%`;
    }
    if (metricName.includes('latency') || metricName.includes('ms')) {
      return `${value.toFixed(0)}ms`;
    }
    if (metricName.includes('memory') && !metricName.includes('percent')) {
      return `${value.toFixed(0)}MB`;
    }
    return value.toFixed(2);
  };

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-4`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 ${colors.bg} rounded-lg ${colors.icon}`}>
            {getMetricIcon(anomaly.metric_type)}
          </div>
          <div>
            <h3 className="text-white font-semibold">
              {anomaly.metric_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${colors.badge}`}>
                {anomaly.severity.toUpperCase()}
              </span>
              {anomaly.related_service && (
                <span className="text-xs text-slate-400">
                  {anomaly.related_service}
                </span>
              )}
            </div>
          </div>
        </div>

        {onDismiss && (
          <button
            onClick={() => onDismiss(anomaly.anomaly_id)}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
            title="Dismiss anomaly"
          >
            <X className="h-4 w-4 text-slate-400" />
          </button>
        )}
      </div>

      {/* Values comparison */}
      <div className="grid grid-cols-3 gap-4 mb-3">
        <div className="bg-slate-900/50 rounded-lg p-3 text-center">
          <p className="text-xs text-slate-500 mb-1">Current</p>
          <p className={`text-lg font-bold ${colors.icon}`}>
            {formatValue(anomaly.current_value, anomaly.metric_name)}
          </p>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-3 text-center">
          <p className="text-xs text-slate-500 mb-1">Expected</p>
          <p className="text-lg font-bold text-slate-300">
            {formatValue(anomaly.expected_value, anomaly.metric_name)}
          </p>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-3 text-center">
          <p className="text-xs text-slate-500 mb-1">Deviation</p>
          <p className={`text-lg font-bold ${colors.icon} flex items-center justify-center gap-1`}>
            <TrendingUp className="h-4 w-4" />
            {anomaly.deviation_percentage > 0 ? '+' : ''}{anomaly.deviation_percentage.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Cause and action */}
      {anomaly.likely_cause && (
        <div className="mb-3">
          <p className="text-xs text-slate-500 mb-1">Likely Cause</p>
          <p className="text-sm text-slate-300">{anomaly.likely_cause}</p>
        </div>
      )}

      {anomaly.recommended_action && (
        <div className="mb-3">
          <p className="text-xs text-slate-500 mb-1">Recommended Action</p>
          <p className="text-sm text-slate-300">{anomaly.recommended_action}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-4">
        {onInvestigate && (
          <button
            onClick={() => onInvestigate(anomaly)}
            className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-semibold transition-all"
          >
            Investigate
          </button>
        )}
        {onCreateIncident && anomaly.severity === 'severe' && (
          <button
            onClick={() => onCreateIncident(anomaly)}
            className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg font-semibold transition-all"
          >
            Create Incident
          </button>
        )}
      </div>

      {/* Timestamp */}
      <p className="text-xs text-slate-500 mt-3 text-center">
        Detected: {new Date(anomaly.detected_at).toLocaleString()}
      </p>
    </div>
  );
}
