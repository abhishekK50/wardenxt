'use client';

import { useState } from 'react';
import {
  Beaker,
  Server,
  Rocket,
  Users,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Play,
  RotateCcw,
  Clock,
  Loader2
} from 'lucide-react';
import { SimulationRequest, SimulationResult } from '@/lib/api';

interface WhatIfSimulatorProps {
  onSimulate: (request: SimulationRequest) => Promise<SimulationResult>;
}

interface ScenarioPreset {
  id: string;
  name: string;
  icon: React.ReactNode;
  scenario: string;
  description: string;
}

const scenarioPresets: ScenarioPreset[] = [
  {
    id: 'deploy',
    name: 'New Deployment',
    icon: <Rocket className="h-5 w-5" />,
    scenario: 'Deploy new version of payment-service to production during peak hours',
    description: 'Simulate deploying a new service version'
  },
  {
    id: 'traffic',
    name: 'Traffic Spike',
    icon: <Users className="h-5 w-5" />,
    scenario: '3x traffic spike to API gateway over 30 minutes',
    description: 'Simulate sudden increase in user traffic'
  },
  {
    id: 'server-failure',
    name: 'Server Failure',
    icon: <Server className="h-5 w-5" />,
    scenario: 'Database primary node becomes unreachable',
    description: 'Simulate critical infrastructure failure'
  },
  {
    id: 'memory-leak',
    name: 'Memory Leak',
    icon: <AlertTriangle className="h-5 w-5" />,
    scenario: 'Memory usage increases 10% per hour in user-service',
    description: 'Simulate gradual resource exhaustion'
  }
];

const timeHorizons = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '12h', label: '12 Hours' },
  { value: '24h', label: '24 Hours' }
];

export default function WhatIfSimulator({ onSimulate }: WhatIfSimulatorProps) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [customScenario, setCustomScenario] = useState('');
  const [timeHorizon, setTimeHorizon] = useState('6h');
  const [isSimulating, setIsSimulating] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getActiveScenario = () => {
    if (selectedPreset) {
      const preset = scenarioPresets.find(p => p.id === selectedPreset);
      return preset?.scenario || '';
    }
    return customScenario;
  };

  const handleSimulate = async () => {
    const scenario = getActiveScenario();
    if (!scenario.trim()) {
      setError('Please select a scenario or enter a custom one');
      return;
    }

    setIsSimulating(true);
    setError(null);

    try {
      const simulationResult = await onSimulate({
        scenario,
        time_horizon: timeHorizon
      });
      setResult(simulationResult);
    } catch (err) {
      setError('Simulation failed. Please try again.');
      console.error('Simulation error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleReset = () => {
    setSelectedPreset(null);
    setCustomScenario('');
    setResult(null);
    setError(null);
  };

  const getProbabilityColor = (prob: number) => {
    if (prob >= 70) return 'text-red-400';
    if (prob >= 40) return 'text-orange-400';
    if (prob >= 20) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getProbabilityBgColor = (prob: number) => {
    if (prob >= 70) return 'bg-red-500/20 border-red-500/30';
    if (prob >= 40) return 'bg-orange-500/20 border-orange-500/30';
    if (prob >= 20) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-green-500/20 border-green-500/30';
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-slate-800/50 p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Beaker className="h-5 w-5 text-purple-400" />
          <h2 className="text-lg font-bold text-white">What-If Simulator</h2>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Test scenarios to predict their impact on system stability
        </p>
      </div>

      <div className="p-4">
        {!result ? (
          <>
            {/* Scenario Presets */}
            <div className="mb-4">
              <label className="text-sm text-slate-400 mb-2 block">Quick Scenarios</label>
              <div className="grid grid-cols-2 gap-2">
                {scenarioPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => {
                      setSelectedPreset(preset.id);
                      setCustomScenario('');
                    }}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      selectedPreset === preset.id
                        ? 'bg-purple-600/20 border-purple-500 text-white'
                        : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={selectedPreset === preset.id ? 'text-purple-400' : 'text-slate-400'}>
                        {preset.icon}
                      </span>
                      <span className="font-medium text-sm">{preset.name}</span>
                    </div>
                    <p className="text-xs text-slate-500">{preset.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Scenario */}
            <div className="mb-4">
              <label className="text-sm text-slate-400 mb-2 block">Or describe a custom scenario</label>
              <textarea
                value={customScenario}
                onChange={(e) => {
                  setCustomScenario(e.target.value);
                  setSelectedPreset(null);
                }}
                placeholder="e.g., Increase database connection pool from 50 to 100..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white text-sm placeholder-slate-500 focus:border-purple-500 focus:outline-none resize-none"
                rows={3}
              />
            </div>

            {/* Time Horizon */}
            <div className="mb-4">
              <label className="text-sm text-slate-400 mb-2 block flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Prediction Time Horizon
              </label>
              <div className="flex gap-2">
                {timeHorizons.map((horizon) => (
                  <button
                    key={horizon.value}
                    onClick={() => setTimeHorizon(horizon.value)}
                    className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                      timeHorizon === horizon.value
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    {horizon.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Simulate Button */}
            <button
              onClick={handleSimulate}
              disabled={isSimulating || (!selectedPreset && !customScenario.trim())}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2"
            >
              {isSimulating ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Running Simulation...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5" />
                  Run Simulation
                </>
              )}
            </button>
          </>
        ) : (
          /* Results View */
          <div className="space-y-4">
            {/* Scenario Summary */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Simulated Scenario</p>
              <p className="text-sm text-white">{result.scenario}</p>
              <p className="text-xs text-slate-500 mt-2">
                Time horizon: {result.time_horizon}
              </p>
            </div>

            {/* Probability Change */}
            <div className="grid grid-cols-3 gap-3">
              <div className={`rounded-lg p-3 border ${getProbabilityBgColor(result.incident_probability_before)}`}>
                <p className="text-xs text-slate-500 mb-1">Before</p>
                <p className={`text-2xl font-bold ${getProbabilityColor(result.incident_probability_before)}`}>
                  {result.incident_probability_before}%
                </p>
              </div>

              <div className="flex items-center justify-center">
                <div className={`flex items-center gap-1 px-3 py-2 rounded-full ${
                  result.probability_change > 0
                    ? 'bg-red-500/20 text-red-400'
                    : result.probability_change < 0
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-slate-700 text-slate-400'
                }`}>
                  {result.probability_change > 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : result.probability_change < 0 ? (
                    <TrendingDown className="h-4 w-4" />
                  ) : null}
                  <span className="font-bold">
                    {result.probability_change > 0 ? '+' : ''}{result.probability_change}%
                  </span>
                </div>
              </div>

              <div className={`rounded-lg p-3 border ${getProbabilityBgColor(result.incident_probability_after)}`}>
                <p className="text-xs text-slate-500 mb-1">After</p>
                <p className={`text-2xl font-bold ${getProbabilityColor(result.incident_probability_after)}`}>
                  {result.incident_probability_after}%
                </p>
              </div>
            </div>

            {/* Predicted Outcome */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Predicted Outcome</p>
              <p className="text-sm text-white">{result.predicted_outcome}</p>
            </div>

            {/* Impact Assessment */}
            <div className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Impact Assessment</p>
              <p className="text-sm text-white">{result.impact_assessment}</p>
            </div>

            {/* Risks and Benefits */}
            <div className="grid grid-cols-2 gap-3">
              {/* Risks */}
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <p className="text-xs text-red-400 font-semibold mb-2 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Risks
                </p>
                <ul className="space-y-1">
                  {result.risks.map((risk, idx) => (
                    <li key={idx} className="text-xs text-slate-300 flex items-start gap-1">
                      <span className="text-red-400 mt-1">•</span>
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Benefits */}
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                <p className="text-xs text-green-400 font-semibold mb-2 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Benefits
                </p>
                <ul className="space-y-1">
                  {result.benefits.map((benefit, idx) => (
                    <li key={idx} className="text-xs text-slate-300 flex items-start gap-1">
                      <span className="text-green-400 mt-1">•</span>
                      {benefit}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
              <p className="text-xs text-blue-400 font-semibold mb-1">Recommendation</p>
              <p className="text-sm text-white">{result.recommendation}</p>
            </div>

            {/* Reset Button */}
            <button
              onClick={handleReset}
              className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <RotateCcw className="h-5 w-5" />
              Run Another Simulation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
