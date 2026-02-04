'use client';

import { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, Clock, Shield, Zap } from 'lucide-react';
import { IncidentPrediction } from '@/lib/api';

interface PredictionCardProps {
  prediction: IncidentPrediction;
  onViewPrevention?: () => void;
}

export default function PredictionCard({ prediction, onViewPrevention }: PredictionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const getProbabilityColor = (probability: number) => {
    if (probability >= 75) return 'border-red-500/50 shadow-red-500/20';
    if (probability >= 50) return 'border-orange-500/50 shadow-orange-500/20';
    if (probability >= 25) return 'border-yellow-500/50 shadow-yellow-500/20';
    return 'border-blue-500/50 shadow-blue-500/20';
  };

  const getProbabilityBadgeColor = (probability: number) => {
    if (probability >= 75) return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (probability >= 50) return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    if (probability >= 25) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'P0':
        return 'bg-red-500/20 text-red-400';
      case 'P1':
        return 'bg-orange-500/20 text-orange-400';
      case 'P2':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-blue-500/20 text-blue-400';
    }
  };

  return (
    <div
      className={`bg-slate-900/50 border-2 rounded-lg overflow-hidden transition-all ${getProbabilityColor(prediction.probability)} shadow-lg`}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-orange-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                {prediction.predicted_incident_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getSeverityColor(prediction.predicted_severity)}`}>
                  {prediction.predicted_severity}
                </span>
                <span className="text-sm text-slate-400">
                  {prediction.time_window || `Next ${prediction.time_horizon}`}
                </span>
              </div>
            </div>
          </div>

          {/* Probability Badge */}
          <div className={`px-4 py-2 rounded-lg border text-center ${getProbabilityBadgeColor(prediction.probability)}`}>
            <span className="text-2xl font-bold">{prediction.probability}%</span>
            <p className="text-xs opacity-80">likely</p>
          </div>
        </div>

        {/* Quick stats */}
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <div className="flex items-center gap-1">
            <Shield className="h-4 w-4" />
            <span>Confidence: {prediction.confidence}%</span>
          </div>
          <div className="flex items-center gap-1">
            <Zap className="h-4 w-4" />
            <span>{prediction.likely_services.length} services at risk</span>
          </div>
        </div>

        {/* Toggle button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-4 w-4" />
              Hide details
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4" />
              View warning signs & actions
            </>
          )}
        </button>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-700 p-4 space-y-4">
          {/* Warning Signs */}
          {prediction.warning_signs.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-yellow-400 mb-2 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Warning Signs to Watch
              </h4>
              <ul className="space-y-1">
                {prediction.warning_signs.map((sign, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-yellow-400">•</span>
                    {sign}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Likely Services */}
          {prediction.likely_services.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-400 mb-2">Services at Risk</h4>
              <div className="flex flex-wrap gap-2">
                {prediction.likely_services.map((service, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-sm"
                  >
                    {service}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Actions */}
          {prediction.recommended_actions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-green-400 mb-2 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Recommended Actions
              </h4>
              <ul className="space-y-1">
                {prediction.recommended_actions.map((action, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-green-400">{idx + 1}.</span>
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Reasoning */}
          {prediction.reasoning && (
            <div>
              <h4 className="text-sm font-semibold text-slate-400 mb-2">AI Analysis</h4>
              <p className="text-sm text-slate-300 bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                {prediction.reasoning}
              </p>
            </div>
          )}

          {/* View Prevention Plan Button */}
          {onViewPrevention && (
            <button
              onClick={onViewPrevention}
              className="w-full mt-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all"
            >
              View Prevention Plan
            </button>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 bg-slate-800/50 flex items-center justify-between text-xs text-slate-500">
        <span>Prediction ID: {prediction.prediction_id}</span>
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {new Date(prediction.predicted_at).toLocaleString()}
        </span>
      </div>
    </div>
  );
}
