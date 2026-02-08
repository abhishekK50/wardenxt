'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Shield,
  Brain,
  AlertTriangle,
  TrendingUp,
  Beaker,
  RefreshCw,
  ChevronRight,
  Activity,
  Clock,
  Zap
} from 'lucide-react';
import { api, RiskScore, IncidentPrediction, Anomaly, PreventiveRecommendation, RiskTrendPoint, SimulationRequest, SimulationResult } from '@/lib/api';
import RiskScoreGauge from '../components/RiskScoreGauge';
import PredictionCard from '../components/PredictionCard';
import AnomalyAlert from '../components/AnomalyAlert';
import PreventiveActionsPanel from '../components/PreventiveActionsPanel';
import RiskTrendChart from '../components/RiskTrendChart';
import WhatIfSimulator from '../components/WhatIfSimulator';

export default function PredictiveDashboard() {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [predictions, setPredictions] = useState<IncidentPrediction[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [recommendations, setRecommendations] = useState<PreventiveRecommendation[]>([]);
  const [riskHistory, setRiskHistory] = useState<RiskTrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'predictions' | 'anomalies' | 'simulator'>('overview');

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [
        riskResult,
        forecastResult,
        anomalyResult,
        recommendationResult,
        historyResult
      ] = await Promise.all([
        api.getRiskScore().catch(() => null),
        api.getPredictionForecast().catch(() => ({ predictions: [] })),
        api.getAnomalies().catch(() => ({ anomalies: [] })),
        api.getRecommendations().catch(() => ({ recommendations: [] })),
        api.getRiskHistory(24).catch(() => ({ history: [] }))
      ]);

      if (riskResult) setRiskScore(riskResult);
      setPredictions(forecastResult.predictions || []);
      setAnomalies(anomalyResult.anomalies || []);
      setRecommendations(recommendationResult.recommendations || []);
      setRiskHistory(historyResult.history || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching predictive data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    // Refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleDismissAnomaly = async (anomalyId: string) => {
    try {
      await api.dismissAnomaly(anomalyId);
      setAnomalies(prev => prev.filter(a => a.anomaly_id !== anomalyId));
    } catch (error) {
      console.error('Error dismissing anomaly:', error);
    }
  };

  const handleSimulate = async (request: SimulationRequest): Promise<SimulationResult> => {
    return api.simulateScenario(request);
  };

  // Calculate summary stats
  const highPriorityPredictions = predictions.filter(p => p.probability >= 60);
  const criticalAnomalies = anomalies.filter(a => a.severity === 'severe' || a.severity === 'moderate');
  const urgentRecommendations = recommendations.filter(r => r.priority === 'urgent' || r.priority === 'high');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Header */}
      <header className="bg-slate-900/80 border-b border-slate-800 sticky top-0 z-50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <Shield className="h-8 w-8 text-green-400" />
                <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-blue-500">
                  WardenXT
                </span>
              </Link>
              <div className="h-6 w-px bg-slate-700" />
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-400" />
                <span className="font-semibold">Predictive Analytics</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Link
                href="/incidents"
                className="text-sm text-slate-400 hover:text-white transition-colors"
              >
                Incidents
              </Link>

              <button
                onClick={fetchData}
                disabled={isLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>

              {lastUpdated && (
                <span className="text-xs text-slate-500">
                  Updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-1 mt-4">
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'predictions', label: 'Predictions', icon: Brain },
              { id: 'anomalies', label: 'Anomalies', icon: AlertTriangle },
              { id: 'simulator', label: 'What-If', icon: Beaker }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-slate-800 text-white border-t border-l border-r border-slate-700'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
                {tab.id === 'anomalies' && criticalAnomalies.length > 0 && (
                  <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
                    {criticalAnomalies.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Quick Stats Banner */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Risk Level</p>
                <p className={`text-2xl font-bold ${
                  riskScore?.level === 'critical' ? 'text-red-400' :
                  riskScore?.level === 'high' ? 'text-orange-400' :
                  riskScore?.level === 'medium' ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {riskScore?.score || '--'}
                </p>
              </div>
              <div className={`p-2 rounded-lg ${
                riskScore?.level === 'critical' ? 'bg-red-500/20' :
                riskScore?.level === 'high' ? 'bg-orange-500/20' :
                riskScore?.level === 'medium' ? 'bg-yellow-500/20' :
                'bg-green-500/20'
              }`}>
                <TrendingUp className={`h-6 w-6 ${
                  riskScore?.level === 'critical' ? 'text-red-400' :
                  riskScore?.level === 'high' ? 'text-orange-400' :
                  riskScore?.level === 'medium' ? 'text-yellow-400' :
                  'text-green-400'
                }`} />
              </div>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Predictions</p>
                <p className="text-2xl font-bold text-purple-400">{highPriorityPredictions.length}</p>
                <p className="text-xs text-slate-500">high probability</p>
              </div>
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Brain className="h-6 w-6 text-purple-400" />
              </div>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Anomalies</p>
                <p className="text-2xl font-bold text-red-400">{criticalAnomalies.length}</p>
                <p className="text-xs text-slate-500">require attention</p>
              </div>
              <div className="p-2 rounded-lg bg-red-500/20">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Actions</p>
                <p className="text-2xl font-bold text-green-400">{urgentRecommendations.length}</p>
                <p className="text-xs text-slate-500">recommended</p>
              </div>
              <div className="p-2 rounded-lg bg-green-500/20">
                <Zap className="h-6 w-6 text-green-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-3 gap-6">
            {/* Left Column - Risk Gauge and Trend */}
            <div className="space-y-6">
              {riskScore && (
                <RiskScoreGauge riskScore={riskScore} />
              )}

              <RiskTrendChart
                data={riskHistory}
                onRefresh={fetchData}
                isLoading={isLoading}
              />
            </div>

            {/* Center Column - Predictions and Anomalies */}
            <div className="space-y-6">
              {/* Top Predictions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-400" />
                    Top Predictions
                  </h3>
                  <button
                    onClick={() => setActiveTab('predictions')}
                    className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    View all <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
                <div className="space-y-3">
                  {predictions.slice(0, 3).map((prediction) => (
                    <PredictionCard
                      key={prediction.prediction_id}
                      prediction={prediction}
                    />
                  ))}
                  {predictions.length === 0 && (
                    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 text-center">
                      <Brain className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                      <p className="text-slate-400 text-sm">No predictions at this time</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Active Anomalies */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-400" />
                    Active Anomalies
                  </h3>
                  <button
                    onClick={() => setActiveTab('anomalies')}
                    className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    View all <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
                <div className="space-y-3">
                  {anomalies.slice(0, 3).map((anomaly) => (
                    <AnomalyAlert
                      key={anomaly.anomaly_id}
                      anomaly={anomaly}
                      onDismiss={handleDismissAnomaly}
                    />
                  ))}
                  {anomalies.length === 0 && (
                    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 text-center">
                      <Activity className="h-8 w-8 text-green-400 mx-auto mb-2" />
                      <p className="text-slate-400 text-sm">All metrics within normal range</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Recommendations and Simulator */}
            <div className="space-y-6">
              <PreventiveActionsPanel
                recommendations={recommendations.slice(0, 5)}
              />

              <WhatIfSimulator onSimulate={handleSimulate} />
            </div>
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Brain className="h-6 w-6 text-purple-400" />
                All Predictions ({predictions.length})
              </h2>
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Clock className="h-4 w-4" />
                Next 24 hours
              </div>
            </div>

            {predictions.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {predictions.map((prediction) => (
                  <PredictionCard
                    key={prediction.prediction_id}
                    prediction={prediction}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-12 text-center">
                <Brain className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No incident predictions at this time</p>
                <p className="text-sm text-slate-500 mt-1">
                  The system is analyzing patterns to predict potential incidents
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'anomalies' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <AlertTriangle className="h-6 w-6 text-red-400" />
                Detected Anomalies ({anomalies.length})
              </h2>
            </div>

            {anomalies.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {anomalies.map((anomaly) => (
                  <AnomalyAlert
                    key={anomaly.anomaly_id}
                    anomaly={anomaly}
                    onDismiss={handleDismissAnomaly}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-12 text-center">
                <Activity className="h-12 w-12 text-green-400 mx-auto mb-3" />
                <p className="text-slate-400">No anomalies detected</p>
                <p className="text-sm text-slate-500 mt-1">
                  All system metrics are within expected ranges
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'simulator' && (
          <div className="max-w-2xl mx-auto">
            <div className="mb-6 text-center">
              <h2 className="text-xl font-bold flex items-center justify-center gap-2">
                <Beaker className="h-6 w-6 text-purple-400" />
                What-If Scenario Simulator
              </h2>
              <p className="text-slate-400 text-sm mt-2">
                Test hypothetical scenarios to understand their potential impact on system stability
              </p>
            </div>

            <WhatIfSimulator onSimulate={handleSimulate} />
          </div>
        )}
      </main>
    </div>
  );
}
