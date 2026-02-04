'use client';

import { useState } from 'react';
import { Shield, Clock, Zap, Play, Calendar, X, ChevronDown, ChevronUp, Copy } from 'lucide-react';
import { PreventiveRecommendation } from '@/lib/api';

interface PreventiveActionsPanelProps {
  recommendations: PreventiveRecommendation[];
  onExecute?: (recommendation: PreventiveRecommendation) => void;
  onSchedule?: (recommendation: PreventiveRecommendation) => void;
  onDismiss?: (recommendationId: string) => void;
}

export default function PreventiveActionsPanel({
  recommendations,
  onExecute,
  onSchedule,
  onDismiss
}: PreventiveActionsPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'priority' | 'impact' | 'effort'>('priority');
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const getPriorityOrder = (priority: string) => {
    const order: Record<string, number> = { urgent: 0, high: 1, medium: 2, low: 3 };
    return order[priority] ?? 4;
  };

  const sortedRecommendations = [...recommendations].sort((a, b) => {
    if (sortBy === 'priority') {
      return getPriorityOrder(a.priority) - getPriorityOrder(b.priority);
    }
    // For impact and effort, we'd need numeric values - using priority as fallback
    return getPriorityOrder(a.priority) - getPriorityOrder(b.priority);
  });

  const copyCommand = async (command: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopiedCommand(command);
      setTimeout(() => setCopiedCommand(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (recommendations.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
        <Shield className="h-12 w-12 text-green-400 mx-auto mb-3" />
        <p className="text-slate-400">No preventive actions needed at this time</p>
        <p className="text-sm text-slate-500 mt-1">System is operating normally</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-slate-800/50 p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-400" />
            <h2 className="text-lg font-bold text-white">Preventive Actions</h2>
            <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full font-semibold">
              {recommendations.length} recommended
            </span>
          </div>

          {/* Sort options */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Sort by:</span>
            {(['priority', 'impact', 'effort'] as const).map((option) => (
              <button
                key={option}
                onClick={() => setSortBy(option)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  sortBy === option
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations list */}
      <div className="divide-y divide-slate-800">
        {sortedRecommendations.map((rec) => {
          const isExpanded = expandedId === rec.recommendation_id;

          return (
            <div key={rec.recommendation_id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold border ${getPriorityColor(rec.priority)}`}>
                      {rec.priority.toUpperCase()}
                    </span>
                    <h3 className="text-white font-semibold">{rec.title}</h3>
                  </div>

                  <p className="text-sm text-slate-400 mb-3">{rec.description}</p>

                  {/* Impact and effort */}
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1 text-green-400">
                      <Zap className="h-4 w-4" />
                      <span>{rec.estimated_impact}</span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-400">
                      <Clock className="h-4 w-4" />
                      <span>{rec.implementation_effort}</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  {onExecute && (
                    <button
                      onClick={() => onExecute(rec)}
                      className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg font-semibold transition-all flex items-center gap-1"
                    >
                      <Play className="h-4 w-4" />
                      Execute
                    </button>
                  )}
                  {onSchedule && (
                    <button
                      onClick={() => onSchedule(rec)}
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-semibold transition-all flex items-center gap-1"
                    >
                      <Calendar className="h-4 w-4" />
                      Schedule
                    </button>
                  )}
                  {onDismiss && (
                    <button
                      onClick={() => onDismiss(rec.recommendation_id)}
                      className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                      title="Dismiss"
                    >
                      <X className="h-4 w-4 text-slate-400" />
                    </button>
                  )}
                </div>
              </div>

              {/* Commands toggle */}
              {rec.commands.length > 0 && (
                <button
                  onClick={() => setExpandedId(isExpanded ? null : rec.recommendation_id)}
                  className="mt-3 flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {isExpanded ? (
                    <>
                      <ChevronUp className="h-4 w-4" />
                      Hide commands
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4" />
                      Show {rec.commands.length} command{rec.commands.length > 1 ? 's' : ''}
                    </>
                  )}
                </button>
              )}

              {/* Commands */}
              {isExpanded && rec.commands.length > 0 && (
                <div className="mt-3 space-y-2">
                  {rec.commands.map((command, idx) => (
                    <div key={idx} className="relative">
                      <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-sm text-green-400 font-mono overflow-x-auto pr-12">
                        {command}
                      </pre>
                      <button
                        onClick={() => copyCommand(command)}
                        className="absolute top-2 right-2 p-2 bg-slate-800 hover:bg-slate-700 rounded transition-colors"
                        title="Copy command"
                      >
                        <Copy className={`h-4 w-4 ${copiedCommand === command ? 'text-green-400' : 'text-slate-400'}`} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Related prediction */}
              {rec.related_prediction_id && (
                <p className="mt-2 text-xs text-slate-500">
                  Related to prediction: {rec.related_prediction_id}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
