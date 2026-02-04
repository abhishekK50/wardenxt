'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { RiskScore } from '@/lib/api';

interface RiskScoreGaugeProps {
  riskScore: RiskScore | null;
  loading?: boolean;
}

export default function RiskScoreGauge({ riskScore, loading }: RiskScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [showFactors, setShowFactors] = useState(false);

  useEffect(() => {
    if (riskScore) {
      // Animate score
      const target = riskScore.score;
      const step = target / 30;
      let current = 0;

      const interval = setInterval(() => {
        current += step;
        if (current >= target) {
          setAnimatedScore(target);
          clearInterval(interval);
        } else {
          setAnimatedScore(Math.round(current));
        }
      }, 20);

      return () => clearInterval(interval);
    }
  }, [riskScore?.score]);

  const getColor = (level: string) => {
    switch (level) {
      case 'low':
        return { main: '#22c55e', bg: 'rgba(34, 197, 94, 0.2)' };
      case 'medium':
        return { main: '#eab308', bg: 'rgba(234, 179, 8, 0.2)' };
      case 'high':
        return { main: '#f97316', bg: 'rgba(249, 115, 22, 0.2)' };
      case 'critical':
        return { main: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)' };
      default:
        return { main: '#64748b', bg: 'rgba(100, 116, 139, 0.2)' };
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-red-400" />;
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-green-400" />;
      default:
        return <Minus className="h-4 w-4 text-slate-400" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 flex flex-col items-center">
        <div className="relative w-48 h-48 animate-pulse">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke="#334155"
              strokeWidth="8"
              fill="none"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-8 w-16 bg-slate-700 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (!riskScore) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 flex flex-col items-center">
        <p className="text-slate-500">No risk data available</p>
      </div>
    );
  }

  const colors = getColor(riskScore.level);
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">System Risk Score</h2>
        <button
          onClick={() => setShowFactors(!showFactors)}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          title="View contributing factors"
        >
          <Info className="h-5 w-5 text-slate-400" />
        </button>
      </div>

      <div className="flex flex-col items-center">
        {/* Gauge */}
        <div className="relative w-48 h-48">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke="#334155"
              strokeWidth="8"
              fill="none"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke={colors.main}
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000 ease-out"
              style={{
                filter: `drop-shadow(0 0 8px ${colors.main})`
              }}
            />
          </svg>

          {/* Center content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="text-5xl font-bold transition-colors"
              style={{ color: colors.main }}
            >
              {animatedScore}
            </span>
            <span
              className="text-sm font-semibold uppercase tracking-wider"
              style={{ color: colors.main }}
            >
              {riskScore.level}
            </span>
          </div>
        </div>

        {/* Trend indicator */}
        <div className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg" style={{ backgroundColor: colors.bg }}>
          {getTrendIcon(riskScore.trend)}
          <span className="text-sm text-white">
            {riskScore.trend === 'increasing' && '+'}
            {riskScore.trend_percentage}% {riskScore.trend}
          </span>
        </div>

        {/* Forecast */}
        {riskScore.forecast_change && (
          <p className="mt-2 text-sm text-slate-400">{riskScore.forecast_change}</p>
        )}
      </div>

      {/* Contributing factors */}
      {showFactors && riskScore.contributing_factors.length > 0 && (
        <div className="mt-6 border-t border-slate-700 pt-4">
          <h3 className="text-sm font-semibold text-slate-400 mb-3">Contributing Factors</h3>
          <div className="space-y-3">
            {riskScore.contributing_factors.map((factor, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white">{factor.name}</span>
                    <span className="text-sm text-slate-400">
                      {Math.round(factor.weighted_score)} pts ({(factor.weight * 100).toFixed(0)}% weight)
                    </span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${factor.score}%`,
                        backgroundColor: factor.score > 70 ? '#ef4444' :
                                        factor.score > 40 ? '#f97316' : '#22c55e'
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{factor.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Last updated */}
      <p className="mt-4 text-xs text-slate-500 text-center">
        Updated: {new Date(riskScore.calculated_at).toLocaleTimeString()}
      </p>
    </div>
  );
}
