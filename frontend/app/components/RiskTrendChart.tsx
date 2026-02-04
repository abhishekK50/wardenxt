'use client';

import { useState, useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Clock, RefreshCw } from 'lucide-react';
import { RiskTrendPoint } from '@/lib/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Legend
} from 'recharts';

interface RiskTrendChartProps {
  data: RiskTrendPoint[];
  forecastData?: RiskTrendPoint[];
  incidents?: Array<{ timestamp: string; title: string }>;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export default function RiskTrendChart({
  data,
  forecastData = [],
  incidents = [],
  onRefresh,
  isLoading = false
}: RiskTrendChartProps) {
  const [timeRange, setTimeRange] = useState<'6h' | '12h' | '24h'>('24h');

  // Format time helper - defined before useMemo that uses it
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Process data for the chart
  const chartData = useMemo(() => {
    const now = new Date();
    let hoursToShow = 24;
    if (timeRange === '6h') hoursToShow = 6;
    if (timeRange === '12h') hoursToShow = 12;

    const cutoff = new Date(now.getTime() - hoursToShow * 60 * 60 * 1000);

    // Filter historical data
    const filtered = data.filter(point => {
      const pointTime = new Date(point.timestamp);
      return pointTime >= cutoff;
    });

    // Format for chart
    const historical = filtered.map(point => ({
      timestamp: point.timestamp,
      time: formatTime(point.timestamp),
      score: point.score,
      level: point.level,
      isForecast: false,
      incidentOccurred: point.incident_occurred
    }));

    // Add forecast data
    const forecast = forecastData.map(point => ({
      timestamp: point.timestamp,
      time: formatTime(point.timestamp),
      forecastScore: point.score,
      level: point.level,
      isForecast: true
    }));

    return [...historical, ...forecast];
  }, [data, forecastData, timeRange]);

  // Calculate trend
  const trend = useMemo(() => {
    if (data.length < 12) return { direction: 'stable', percentage: 0 };

    const recent = data.slice(-12);
    const previous = data.slice(-24, -12);

    if (previous.length === 0) return { direction: 'stable', percentage: 0 };

    const recentAvg = recent.reduce((a, b) => a + b.score, 0) / recent.length;
    const previousAvg = previous.reduce((a, b) => a + b.score, 0) / previous.length;

    const change = previousAvg > 0 ? ((recentAvg - previousAvg) / previousAvg) * 100 : 0;

    if (change > 10) return { direction: 'increasing', percentage: change };
    if (change < -10) return { direction: 'decreasing', percentage: change };
    return { direction: 'stable', percentage: change };
  }, [data]);

  // Get current score
  const currentScore = data.length > 0 ? data[data.length - 1].score : 0;
  const currentLevel = data.length > 0 ? data[data.length - 1].level : 'low';

  const getTrendIcon = () => {
    switch (trend.direction) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-red-400" />;
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-green-400" />;
      default:
        return <Minus className="h-4 w-4 text-slate-400" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      default: return 'text-green-400';
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const isForecast = data.isForecast;
      const score = isForecast ? data.forecastScore : data.score;

      return (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl">
          <p className="text-slate-400 text-xs mb-1">
            {isForecast ? 'Forecast' : 'Historical'} - {label}
          </p>
          <p className="text-white font-bold text-lg">
            Risk Score: {score}
          </p>
          <p className={`text-sm ${getLevelColor(data.level)}`}>
            Level: {data.level?.toUpperCase()}
          </p>
          {data.incidentOccurred && (
            <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              Incident occurred at this time
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
        <Clock className="h-12 w-12 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400">No risk history data available</p>
        <p className="text-sm text-slate-500 mt-1">Data will appear as the system collects metrics</p>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
          >
            Check for Data
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-slate-800/50 p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-white">Risk Trend</h2>
            <div className={`flex items-center gap-1 px-2 py-1 rounded ${
              trend.direction === 'increasing' ? 'bg-red-500/20' :
              trend.direction === 'decreasing' ? 'bg-green-500/20' : 'bg-slate-700'
            }`}>
              {getTrendIcon()}
              <span className={`text-sm font-medium ${
                trend.direction === 'increasing' ? 'text-red-400' :
                trend.direction === 'decreasing' ? 'text-green-400' : 'text-slate-400'
              }`}>
                {trend.percentage > 0 ? '+' : ''}{trend.percentage.toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Time range selector */}
            <div className="flex bg-slate-800 rounded-lg p-1">
              {(['6h', '12h', '24h'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 text-xs rounded transition-colors ${
                    timeRange === range
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>

            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isLoading}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
                title="Refresh data"
              >
                <RefreshCw className={`h-4 w-4 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        </div>

        {/* Current status summary */}
        <div className="mt-3 flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Current:</span>
            <span className={`font-bold ${getLevelColor(currentLevel)}`}>
              {currentScore}
            </span>
            <span className={`px-2 py-0.5 rounded text-xs ${
              currentLevel === 'critical' ? 'bg-red-500/20 text-red-400' :
              currentLevel === 'high' ? 'bg-orange-500/20 text-orange-400' :
              currentLevel === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-green-500/20 text-green-400'
            }`}>
              {currentLevel.toUpperCase()}
            </span>
          </div>

          {forecastData.length > 0 && (
            <div className="flex items-center gap-2 text-slate-400">
              <span>Forecast:</span>
              <span className="text-white font-medium">
                {forecastData[forecastData.length - 1]?.score || '-'}
              </span>
              <span className="text-xs text-slate-500">(+6h)</span>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="p-4">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

              {/* Risk level zones */}
              <ReferenceArea y1={0} y2={25} fill="#22c55e" fillOpacity={0.1} />
              <ReferenceArea y1={25} y2={50} fill="#eab308" fillOpacity={0.1} />
              <ReferenceArea y1={50} y2={75} fill="#f97316" fillOpacity={0.1} />
              <ReferenceArea y1={75} y2={100} fill="#ef4444" fillOpacity={0.1} />

              {/* Threshold lines */}
              <ReferenceLine y={25} stroke="#22c55e" strokeDasharray="5 5" strokeOpacity={0.5} />
              <ReferenceLine y={50} stroke="#eab308" strokeDasharray="5 5" strokeOpacity={0.5} />
              <ReferenceLine y={75} stroke="#f97316" strokeDasharray="5 5" strokeOpacity={0.5} />

              {/* Incident markers */}
              {incidents.map((incident, idx) => (
                <ReferenceLine
                  key={idx}
                  x={formatTime(incident.timestamp)}
                  stroke="#ef4444"
                  strokeWidth={2}
                  label={{ value: '!', position: 'top', fill: '#ef4444', fontSize: 12 }}
                />
              ))}

              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#475569' }}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#475569' }}
                ticks={[0, 25, 50, 75, 100]}
              />

              <Tooltip content={<CustomTooltip />} />

              <Legend
                verticalAlign="top"
                height={36}
                formatter={(value) => <span className="text-slate-400 text-xs">{value}</span>}
              />

              {/* Historical risk line */}
              <Line
                type="monotone"
                dataKey="score"
                name="Risk Score"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: '#3b82f6', stroke: '#1e40af' }}
              />

              {/* Forecast line */}
              <Line
                type="monotone"
                dataKey="forecastScore"
                name="Forecast"
                stroke="#8b5cf6"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                activeDot={{ r: 6, fill: '#8b5cf6', stroke: '#6d28d9' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Legend for risk zones */}
        <div className="mt-4 flex items-center justify-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500/30 rounded" />
            <span className="text-slate-400">Low (0-25)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-yellow-500/30 rounded" />
            <span className="text-slate-400">Medium (25-50)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-orange-500/30 rounded" />
            <span className="text-slate-400">High (50-75)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500/30 rounded" />
            <span className="text-slate-400">Critical (75-100)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
