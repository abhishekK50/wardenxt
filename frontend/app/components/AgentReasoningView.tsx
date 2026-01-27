'use client';

import { Brain, Sparkles, CheckCircle, Loader2 } from 'lucide-react';
import { useAgentStatus } from '@/lib/hooks/useAgentStatus';

interface AgentReasoningViewProps {
  incidentId: string;
  isAnalyzing: boolean;
}

export default function AgentReasoningView({ incidentId, isAnalyzing }: AgentReasoningViewProps) {
  const { status, reasoningSteps, isConnected, error } = useAgentStatus(
    incidentId,
    isAnalyzing
  );

  if (!isAnalyzing && (!status || status.status === 'IDLE')) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-lg p-6 shadow-xl shadow-purple-500/10">
      <div className="flex items-center gap-3 mb-4">
        <Brain className="h-6 w-6 text-purple-400" />
        <h2 className="text-2xl font-bold text-white">AI Agent Reasoning</h2>
        {isConnected ? (
          <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
            Live
          </span>
        ) : (
          <span className="px-2 py-1 bg-slate-500/20 text-slate-400 text-xs rounded-full border border-slate-500/30">
            Disconnected
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Current Status */}
      {status && (
        <div className="mb-6 bg-slate-900/50 rounded-lg p-4 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {status.status === 'ANALYZING' ? (
                <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-400" />
              )}
              <span className="text-sm font-semibold text-slate-300">
                {status.status}
              </span>
            </div>
            <span className="text-xs text-slate-500">
              {Math.round(status.progress * 100)}%
            </span>
          </div>

          {status.current_task && (
            <p className="text-slate-400 text-sm mt-2">{status.current_task}</p>
          )}

          {/* Progress Bar */}
          <div className="mt-3 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
              style={{ width: `${status.progress * 100}%` }}
            />
          </div>

          {/* Stats */}
          <div className="flex gap-4 mt-3 text-xs text-slate-500">
            {status.logs_analyzed > 0 && (
              <span>Logs: {status.logs_analyzed}</span>
            )}
            {status.metrics_analyzed > 0 && (
              <span>Metrics: {status.metrics_analyzed}</span>
            )}
          </div>
        </div>
      )}

      {/* Reasoning Steps */}
      {reasoningSteps.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-5 w-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">Reasoning Steps</h3>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {reasoningSteps.map((step, index) => (
              <div
                key={index}
                className="flex items-start gap-3 bg-slate-900/50 rounded-lg p-3 border border-slate-800 hover:border-purple-500/50 transition-colors"
              >
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-semibold text-purple-400">
                    {index + 1}
                  </span>
                </div>
                <p className="text-slate-300 text-sm flex-1">{step}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {reasoningSteps.length === 0 && status?.status === 'ANALYZING' && (
        <div className="text-center py-8 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-purple-400" />
          <p className="text-sm">Agent is analyzing... Reasoning steps will appear here</p>
        </div>
      )}
    </div>
  );
}
