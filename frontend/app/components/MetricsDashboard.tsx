'use client';

import { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, Activity, Cpu, HardDrive, Zap } from 'lucide-react';

interface MetricPoint {
  index: number;
  cpu: number;
  memory: number;
  requests: number;
  errors: number;
  time: string;
  timestamp?: string;
}

interface MetricsDashboardProps {
  metrics: MetricPoint[];
  incidentStartTime?: string;
}

interface Anomaly {
  metric: string;
  timestamp: string;
  value: number;
  threshold: number;
  severity: 'high' | 'medium' | 'low';
}

export default function MetricsDashboard({ metrics, incidentStartTime }: MetricsDashboardProps) {
  const [selectedMetric, setSelectedMetric] = useState<'all' | 'cpu' | 'memory' | 'requests' | 'errors'>('all');
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('line');

  // Calculate anomalies
  const anomalies = useMemo(() => {
    if (metrics.length === 0) return [];

    const detected: Anomaly[] = [];
    const thresholds = {
      cpu: 80,
      memory: 2000, // MB
      requests: 1000, // req/s
      errors: 5, // %
    };

    metrics.forEach((point) => {
      // CPU anomalies
      if (point.cpu > thresholds.cpu) {
        detected.push({
          metric: 'cpu',
          timestamp: point.time,
          value: point.cpu,
          threshold: thresholds.cpu,
          severity: point.cpu > 90 ? 'high' : point.cpu > 85 ? 'medium' : 'low',
        });
      }

      // Memory anomalies
      if (point.memory > thresholds.memory) {
        detected.push({
          metric: 'memory',
          timestamp: point.time,
          value: point.memory,
          threshold: thresholds.memory,
          severity: point.memory > 3000 ? 'high' : point.memory > 2500 ? 'medium' : 'low',
        });
      }

      // Error rate anomalies
      if (point.errors > thresholds.errors) {
        detected.push({
          metric: 'errors',
          timestamp: point.time,
          value: point.errors,
          threshold: thresholds.errors,
          severity: point.errors > 10 ? 'high' : point.errors > 7 ? 'medium' : 'low',
        });
      }
    });

    return detected;
  }, [metrics]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (metrics.length === 0) {
      return {
        cpu: { avg: 0, max: 0, min: 0, trend: 0 },
        memory: { avg: 0, max: 0, min: 0, trend: 0 },
        requests: { avg: 0, max: 0, min: 0, trend: 0 },
        errors: { avg: 0, max: 0, min: 0, trend: 0 },
      };
    }

    const calculateStats = (key: keyof MetricPoint) => {
      const values = metrics.map((m) => m[key] as number);
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      const max = Math.max(...values);
      const min = Math.min(...values);
      const firstHalf = values.slice(0, Math.floor(values.length / 2));
      const secondHalf = values.slice(Math.floor(values.length / 2));
      const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
      const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
      const trend = ((secondAvg - firstAvg) / firstAvg) * 100;

      return { avg, max, min, trend };
    };

    return {
      cpu: calculateStats('cpu'),
      memory: calculateStats('memory'),
      requests: calculateStats('requests'),
      errors: calculateStats('errors'),
    };
  }, [metrics]);

  // Filter metrics based on selection
  const filteredMetrics = useMemo(() => {
    if (selectedMetric === 'all') return metrics;
    return metrics.map((m) => ({
      ...m,
      [selectedMetric]: m[selectedMetric],
    }));
  }, [metrics, selectedMetric]);

  const renderChart = () => {
    const commonProps = {
      data: filteredMetrics,
      margin: { top: 5, right: 30, left: 20, bottom: 5 },
    };

    if (chartType === 'area') {
      return (
        <AreaChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
          />
          <Legend />
          {selectedMetric === 'all' || selectedMetric === 'cpu' ? (
            <Area
              type="monotone"
              dataKey="cpu"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.2}
              name="CPU %"
            />
          ) : null}
          {selectedMetric === 'all' || selectedMetric === 'memory' ? (
            <Area
              type="monotone"
              dataKey="memory"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.2}
              name="Memory MB"
            />
          ) : null}
          {selectedMetric === 'all' || selectedMetric === 'requests' ? (
            <Area
              type="monotone"
              dataKey="requests"
              stroke="#f59e0b"
              fill="#f59e0b"
              fillOpacity={0.2}
              name="Requests/s"
            />
          ) : null}
          {selectedMetric === 'all' || selectedMetric === 'errors' ? (
            <Area
              type="monotone"
              dataKey="errors"
              stroke="#ef4444"
              fill="#ef4444"
              fillOpacity={0.2}
              name="Error Rate %"
            />
          ) : null}
        </AreaChart>
      );
    }

    if (chartType === 'bar') {
      return (
        <BarChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" stroke="#64748b" />
          <YAxis stroke="#64748b" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
          />
          <Legend />
          {selectedMetric === 'all' || selectedMetric === 'cpu' ? (
            <Bar dataKey="cpu" fill="#3b82f6" name="CPU %" />
          ) : null}
          {selectedMetric === 'all' || selectedMetric === 'memory' ? (
            <Bar dataKey="memory" fill="#10b981" name="Memory MB" />
          ) : null}
          {selectedMetric === 'all' || selectedMetric === 'requests' ? (
            <Bar dataKey="requests" fill="#f59e0b" name="Requests/s" />
          ) : null}
          {selectedMetric === 'all' || selectedMetric === 'errors' ? (
            <Bar dataKey="errors" fill="#ef4444" name="Error Rate %" />
          ) : null}
        </BarChart>
      );
    }

    // Default: Line chart
    return (
      <LineChart {...commonProps}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" stroke="#64748b" />
        <YAxis stroke="#64748b" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
          }}
        />
        <Legend />
        {selectedMetric === 'all' || selectedMetric === 'cpu' ? (
          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#3b82f6"
            strokeWidth={2}
            name="CPU %"
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ) : null}
        {selectedMetric === 'all' || selectedMetric === 'memory' ? (
          <Line
            type="monotone"
            dataKey="memory"
            stroke="#10b981"
            strokeWidth={2}
            name="Memory MB"
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ) : null}
        {selectedMetric === 'all' || selectedMetric === 'requests' ? (
          <Line
            type="monotone"
            dataKey="requests"
            stroke="#f59e0b"
            strokeWidth={2}
            name="Requests/s"
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ) : null}
        {selectedMetric === 'all' || selectedMetric === 'errors' ? (
          <Line
            type="monotone"
            dataKey="errors"
            stroke="#ef4444"
            strokeWidth={2}
            name="Error Rate %"
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ) : null}
        {/* Threshold lines */}
        {selectedMetric === 'cpu' || selectedMetric === 'all' ? (
          <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="5 5" label="CPU Threshold" />
        ) : null}
        {selectedMetric === 'errors' || selectedMetric === 'all' ? (
          <ReferenceLine y={5} stroke="#ef4444" strokeDasharray="5 5" label="Error Threshold" />
        ) : null}
      </LineChart>
    );
  };

  if (metrics.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <p className="text-slate-500 text-center">No metrics data available</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white">System Metrics Dashboard</h2>
        <div className="flex items-center gap-2">
          {/* Chart Type Selector */}
          <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
            {(['line', 'area', 'bar'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setChartType(type)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  chartType === type
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Metric Selector */}
      <div className="flex flex-wrap gap-2 mb-6">
        {(['all', 'cpu', 'memory', 'requests', 'errors'] as const).map((metric) => (
          <button
            key={metric}
            onClick={() => setSelectedMetric(metric)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedMetric === metric
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {metric.charAt(0).toUpperCase() + metric.slice(1)}
          </button>
        ))}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-4 w-4 text-blue-400" />
            <span className="text-xs text-slate-400">CPU</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-white">{stats.cpu.avg.toFixed(1)}%</span>
            {stats.cpu.trend > 0 ? (
              <TrendingUp className="h-4 w-4 text-red-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-green-400" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">Max: {stats.cpu.max.toFixed(1)}%</p>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <HardDrive className="h-4 w-4 text-green-400" />
            <span className="text-xs text-slate-400">Memory</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-white">{stats.memory.avg.toFixed(0)} MB</span>
            {stats.memory.trend > 0 ? (
              <TrendingUp className="h-4 w-4 text-red-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-green-400" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">Max: {stats.memory.max.toFixed(0)} MB</p>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="h-4 w-4 text-yellow-400" />
            <span className="text-xs text-slate-400">Requests</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-white">{stats.requests.avg.toFixed(0)}/s</span>
            {stats.requests.trend > 0 ? (
              <TrendingUp className="h-4 w-4 text-green-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-400" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">Max: {stats.requests.max.toFixed(0)}/s</p>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <span className="text-xs text-slate-400">Errors</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-white">{stats.errors.avg.toFixed(2)}%</span>
            {stats.errors.trend > 0 ? (
              <TrendingUp className="h-4 w-4 text-red-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-green-400" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">Max: {stats.errors.max.toFixed(2)}%</p>
        </div>
      </div>

      {/* Anomalies Alert */}
      {anomalies.length > 0 && (
        <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <h3 className="text-sm font-semibold text-red-400">
              {anomalies.length} Anomaly{anomalies.length > 1 ? 'ies' : ''} Detected
            </h3>
          </div>
          <div className="space-y-1">
            {anomalies.slice(0, 3).map((anomaly, i) => (
              <div key={i} className="text-xs text-slate-300">
                <span className="font-semibold">{anomaly.metric.toUpperCase()}</span> exceeded threshold (
                {anomaly.value.toFixed(1)} &gt; {anomaly.threshold}) at {anomaly.timestamp}
              </div>
            ))}
            {anomalies.length > 3 && (
              <div className="text-xs text-slate-500">+{anomalies.length - 3} more anomalies</div>
            )}
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
