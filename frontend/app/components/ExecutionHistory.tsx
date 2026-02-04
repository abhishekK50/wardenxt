'use client';

import { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, ChevronDown, ChevronUp, Filter } from 'lucide-react';
import { useAPI } from '@/lib/hooks/useAPI';
import { ExecutionResult } from '@/lib/api';

interface ExecutionHistoryProps {
  incidentId: string;
}

export default function ExecutionHistory({ incidentId }: ExecutionHistoryProps) {
  const api = useAPI();
  const [history, setHistory] = useState<ExecutionResult[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    successful: 0,
    failed: 0,
    dryRun: 0
  });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'successful' | 'failed'>('all');
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchHistory();
  }, [incidentId]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getRunbookExecutionHistory(incidentId);
      setHistory(data.history || []);
      setStats({
        total: data.executions_count || 0,
        successful: data.successful_count || 0,
        failed: data.failed_count || 0,
        dryRun: data.dry_run_count || 0
      });
    } catch (error) {
      console.error('Failed to fetch execution history:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };

  const filteredHistory = history.filter(result => {
    if (filter === 'successful') return result.success;
    if (filter === 'failed') return !result.success;
    return true;
  });

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
        <p className="text-slate-400 mt-3">Loading execution history...</p>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
        <Clock className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400">No commands have been executed yet</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-slate-800/50 p-6 border-b border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Execution History</h2>
          <button
            onClick={fetchHistory}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-all"
          >
            Refresh
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-900/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-1">Total Executions</p>
            <p className="text-2xl font-bold text-white">{stats.total}</p>
          </div>
          <div className="bg-green-500/10 rounded-lg p-4">
            <p className="text-green-400 text-sm mb-1">Successful</p>
            <p className="text-2xl font-bold text-green-400">{stats.successful}</p>
          </div>
          <div className="bg-red-500/10 rounded-lg p-4">
            <p className="text-red-400 text-sm mb-1">Failed</p>
            <p className="text-2xl font-bold text-red-400">{stats.failed}</p>
          </div>
          <div className="bg-blue-500/10 rounded-lg p-4">
            <p className="text-blue-400 text-sm mb-1">Dry Runs</p>
            <p className="text-2xl font-bold text-blue-400">{stats.dryRun}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mt-4">
          <Filter className="h-4 w-4 text-slate-400" />
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-lg text-sm font-semibold transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('successful')}
            className={`px-3 py-1 rounded-lg text-sm font-semibold transition-colors ${
              filter === 'successful'
                ? 'bg-green-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            Successful
          </button>
          <button
            onClick={() => setFilter('failed')}
            className={`px-3 py-1 rounded-lg text-sm font-semibold transition-colors ${
              filter === 'failed'
                ? 'bg-red-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            Failed
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div className="divide-y divide-slate-800">
        {filteredHistory.map((result, index) => {
          const isExpanded = expandedResults.has(index);
          const timestamp = new Date(result.executed_at).toLocaleString();

          return (
            <div key={index} className="p-4 hover:bg-slate-800/30 transition-colors">
              <button
                onClick={() => toggleExpanded(index)}
                className="w-full flex items-start gap-4"
              >
                <div className="flex-shrink-0 mt-1">
                  {result.success ? (
                    <CheckCircle className="h-5 w-5 text-green-400" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-400" />
                  )}
                </div>

                <div className="flex-1 text-left">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-white font-semibold">
                      Step {result.step_number}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-sm text-slate-400">{timestamp}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-sm text-slate-400">
                      {result.duration_seconds.toFixed(2)}s
                    </span>
                    {result.dry_run && (
                      <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded font-semibold">
                        DRY RUN
                      </span>
                    )}
                  </div>

                  <code className="text-sm text-green-400 font-mono block truncate">
                    {result.command}
                  </code>

                  {result.executed_by && (
                    <p className="text-xs text-slate-500 mt-1">
                      Executed by: {result.executed_by}
                    </p>
                  )}
                </div>

                <div className="flex-shrink-0">
                  {isExpanded ? (
                    <ChevronUp className="h-5 w-5 text-slate-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-slate-400" />
                  )}
                </div>
              </button>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-4 ml-9 space-y-3">
                  {/* Full Command */}
                  <div>
                    <p className="text-xs text-slate-500 mb-2">Full Command:</p>
                    <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-sm text-green-400 font-mono overflow-x-auto">
                      {result.command}
                    </pre>
                  </div>

                  {/* Output */}
                  {result.output && (
                    <div>
                      <p className="text-xs text-slate-500 mb-2">Output:</p>
                      <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-sm text-slate-300 font-mono overflow-x-auto max-h-64 overflow-y-auto">
                        {result.output}
                      </pre>
                    </div>
                  )}

                  {/* Error */}
                  {result.error && (
                    <div>
                      <p className="text-xs text-red-400 mb-2">Error:</p>
                      <pre className="bg-slate-950 border border-red-800 rounded p-3 text-sm text-red-300 font-mono overflow-x-auto">
                        {result.error}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
