'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, Clock, DollarSign, Users, TrendingUp, ChevronRight, Activity, Zap, Volume2, Loader2, Brain, Shield } from 'lucide-react';
import { useAPI } from '@/lib/hooks/useAPI';
import { useToast } from '@/app/components/ErrorToast';
import StatusBadge, { IncidentStatus } from '@/app/components/StatusBadge';
import LiveIncidentFeed from '@/app/components/LiveIncidentFeed';
import VoiceCommander from '@/app/components/VoiceCommander';
import { api as apiClient, RiskScore } from '@/lib/api';

interface Incident {
  incident_id: string;
  title: string;
  severity: string;
  status: IncidentStatus;
  incident_type: string;
  start_time: string;
  duration_minutes: number;
  services_affected: string[];
  estimated_cost: string;
  users_impacted: string;
  mttr_actual: string;
}

// Helper to calculate live duration from start time
function calculateLiveDuration(startTime: string | undefined): { hours: number; minutes: number; totalMinutes: number } {
  if (!startTime) {
    return { hours: 0, minutes: 0, totalMinutes: 0 };
  }

  const start = new Date(startTime).getTime();
  const now = Date.now();
  const diffMs = Math.max(0, now - start);

  const totalMinutes = Math.floor(diffMs / 1000 / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  return { hours, minutes, totalMinutes };
}

// Check if incident is active (not resolved/closed)
function isIncidentActive(status: string | undefined): boolean {
  if (!status) return true;
  const resolvedStatuses = ['RESOLVED', 'CLOSED'];
  return !resolvedStatuses.includes(status.toUpperCase());
}

const severityColors = {
  P0: 'bg-red-500/10 text-red-400 border-red-500/30',
  P1: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  P2: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  P3: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
};

const severityGlow = {
  P0: 'shadow-lg shadow-red-500/20',
  P1: 'shadow-lg shadow-orange-500/20',
  P2: 'shadow-lg shadow-yellow-500/20',
  P3: 'shadow-lg shadow-blue-500/20',
};

const incidentTypeLabels: Record<string, string> = {
  bmr_recovery: 'Hardware Failure',
  connection_pool_exhaustion: 'Resource Exhaustion',
  memory_leak: 'Memory Management',
  dns_propagation: 'Network Infrastructure',
  kubernetes_crashloop: 'Container Orchestration',
};

const incidentTypeIcons: Record<string, any> = {
  bmr_recovery: Activity,
  connection_pool_exhaustion: TrendingUp,
  memory_leak: AlertCircle,
  dns_propagation: Zap,
  kubernetes_crashloop: Activity,
};

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playingIncidentId, setPlayingIncidentId] = useState<string | null>(null);
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [liveDurations, setLiveDurations] = useState<Record<string, { hours: number; minutes: number; totalMinutes: number }>>({});
  const [currentTime, setCurrentTime] = useState(Date.now());
  const api = useAPI();
  const { showToast, ToastContainer } = useToast();

  useEffect(() => {
    fetchIncidents();
    fetchRiskScore();
  }, []);

  // Update live durations every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());

      // Recalculate durations for all active incidents
      const newDurations: Record<string, { hours: number; minutes: number; totalMinutes: number }> = {};
      incidents.forEach(inc => {
        if (isIncidentActive(inc.status) && inc.start_time) {
          newDurations[inc.incident_id] = calculateLiveDuration(inc.start_time);
        } else {
          newDurations[inc.incident_id] = {
            hours: Math.floor(inc.duration_minutes / 60),
            minutes: inc.duration_minutes % 60,
            totalMinutes: inc.duration_minutes
          };
        }
      });
      setLiveDurations(newDurations);
    }, 30000); // Update every 30 seconds

    // Initial calculation
    const initialDurations: Record<string, { hours: number; minutes: number; totalMinutes: number }> = {};
    incidents.forEach(inc => {
      if (isIncidentActive(inc.status) && inc.start_time) {
        initialDurations[inc.incident_id] = calculateLiveDuration(inc.start_time);
      } else {
        initialDurations[inc.incident_id] = {
          hours: Math.floor(inc.duration_minutes / 60),
          minutes: inc.duration_minutes % 60,
          totalMinutes: inc.duration_minutes
        };
      }
    });
    setLiveDurations(initialDurations);

    return () => clearInterval(interval);
  }, [incidents]);

  const fetchRiskScore = async () => {
    try {
      const score = await apiClient.getRiskScore();
      setRiskScore(score);
    } catch (err) {
      console.log('Risk score not available');
    }
  };

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.listIncidents();
      // Map API response to our Incident interface
      setIncidents(response.incidents.map((inc: any) => ({
        ...inc,
        status: inc.status || 'DETECTED',
        incident_type: inc.incident_type || 'unknown',
        start_time: inc.start_time || '',
        mttr_actual: inc.mttr_actual || 'Unknown',
      })) as Incident[]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load incidents';
      console.error('Error fetching incidents:', err);
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handlePlaySummary = async (incidentId: string, event: React.MouseEvent) => {
    // Prevent card click
    event.preventDefault();
    event.stopPropagation();

    if (playingIncidentId === incidentId) {
      // Stop current playback
      window.speechSynthesis.cancel();
      setPlayingIncidentId(null);
      return;
    }

    try {
      setPlayingIncidentId(incidentId);

      // Get summary text from backend
      const summaryData = await api.getIncidentAudioSummary(incidentId);

      // Check if browser supports speech synthesis
      if (!('speechSynthesis' in window)) {
        showToast('Your browser does not support text-to-speech', 'error');
        setPlayingIncidentId(null);
        return;
      }

      // Create utterance for browser TTS
      const utterance = new SpeechSynthesisUtterance(summaryData.summary_text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Try to use a good English voice
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
        || voices.find(v => v.lang.startsWith('en'));
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onend = () => {
        setPlayingIncidentId(null);
      };

      utterance.onerror = (err) => {
        console.error('Speech synthesis error:', err);
        setPlayingIncidentId(null);
        showToast('Failed to play audio summary', 'error');
      };

      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error('Failed to get audio summary:', err);
      setPlayingIncidentId(null);
      showToast(err instanceof Error ? err.message : 'Failed to play summary', 'error');
    }
  };

  if (loading) {
    return (
      <>
        <ToastContainer />
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
          <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
            <div className="max-w-7xl mx-auto px-6 py-6">
              <div className="h-8 bg-slate-800 rounded w-48 animate-pulse"></div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-6 py-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 animate-pulse">
                  <div className="h-4 bg-slate-800 rounded w-1/2 mb-2"></div>
                  <div className="h-8 bg-slate-800 rounded w-3/4"></div>
                </div>
              ))}
            </div>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 animate-pulse">
                  <div className="h-6 bg-slate-800 rounded w-1/3 mb-4"></div>
                  <div className="h-4 bg-slate-800 rounded w-full mb-2"></div>
                  <div className="h-4 bg-slate-800 rounded w-5/6"></div>
                </div>
              ))}
            </div>
          </main>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <ToastContainer />
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
          <div className="text-center max-w-md">
            <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Failed to Load Incidents</h2>
            <p className="text-slate-400 mb-6">{error}</p>
            <button
              onClick={fetchIncidents}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Retry
            </button>
            <p className="text-sm text-slate-500 mt-4">
              Make sure the backend is running
            </p>
          </div>
        </div>
      </>
    );
  }

  const stats = {
    total: incidents.length,
    p1: incidents.filter(i => i.severity === 'P1').length,
    p2: incidents.filter(i => i.severity === 'P2').length,
    investigating: incidents.filter(i => ['DETECTED', 'INVESTIGATING'].includes(i.status)).length,
    resolved: incidents.filter(i => ['RESOLVED', 'CLOSED'].includes(i.status)).length,
    totalCost: incidents.reduce((sum, i) => {
      const cost = parseInt(i.estimated_cost.replace(/[$,]/g, ''));
      return sum + (isNaN(cost) ? 0 : cost);
    }, 0),
  };

  return (
    <>
      <ToastContainer />
      <LiveIncidentFeed />
      <VoiceCommander />
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        {/* Header */}
        <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-1">
                  <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    WardenXT
                  </span>
                </h1>
                <p className="text-slate-400">
                  AI-Powered Incident Commander for P0/P1/P2 Critical Incidents
                </p>
              </div>
              <div className="flex items-center gap-4">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-purple-400 hover:text-purple-300 transition-all"
                >
                  <Brain className="h-4 w-4" />
                  <span className="text-sm font-medium">Predictive Analytics</span>
                  {riskScore && riskScore.level !== 'low' && (
                    <span className={`px-1.5 py-0.5 text-xs rounded ${
                      riskScore.level === 'critical' ? 'bg-red-500 text-white' :
                      riskScore.level === 'high' ? 'bg-orange-500 text-white' :
                      'bg-yellow-500 text-black'
                    }`}>
                      {riskScore.score}
                    </span>
                  )}
                </Link>
                <div className="h-6 w-px bg-slate-700" />
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-500">Powered by</span>
                  <span className="text-lg font-semibold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    Gemini 3 Flash Preview
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-8">
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-blue-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-blue-400" />
                </div>
                <span className="text-slate-400 text-sm font-medium">Total Incidents</span>
              </div>
              <p className="text-4xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-slate-500 mt-2">Active monitoring</p>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-orange-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/10">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-orange-500/10 rounded-lg">
                  <Activity className="h-5 w-5 text-orange-400" />
                </div>
                <span className="text-slate-400 text-sm font-medium">Investigating</span>
              </div>
              <p className="text-4xl font-bold text-white">{stats.investigating}</p>
              <p className="text-xs text-slate-500 mt-2">Active incidents</p>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-green-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-green-500/10">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-green-500/10 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                </div>
                <span className="text-slate-400 text-sm font-medium">Resolved</span>
              </div>
              <p className="text-4xl font-bold text-white">{stats.resolved}</p>
              <p className="text-xs text-slate-500 mt-2">Completed incidents</p>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-yellow-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-yellow-500/10">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-yellow-500/10 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-yellow-400" />
                </div>
                <span className="text-slate-400 text-sm font-medium">P1/P2</span>
              </div>
              <p className="text-4xl font-bold text-white">{stats.p1 + stats.p2}</p>
              <p className="text-xs text-slate-500 mt-2">Critical priority</p>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-red-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-red-500/10">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-red-500/10 rounded-lg">
                  <DollarSign className="h-5 w-5 text-red-400" />
                </div>
                <span className="text-slate-400 text-sm font-medium">Total Impact</span>
              </div>
              <p className="text-4xl font-bold text-white">
                ${(stats.totalCost / 1000000).toFixed(1)}M
              </p>
              <p className="text-xs text-slate-500 mt-2">Estimated business cost</p>
            </div>

            {/* Risk Score Widget */}
            <Link
              href="/dashboard"
              className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-purple-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10 group cursor-pointer"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${
                  riskScore?.level === 'critical' ? 'bg-red-500/10' :
                  riskScore?.level === 'high' ? 'bg-orange-500/10' :
                  riskScore?.level === 'medium' ? 'bg-yellow-500/10' :
                  'bg-green-500/10'
                }`}>
                  <Shield className={`h-5 w-5 ${
                    riskScore?.level === 'critical' ? 'text-red-400' :
                    riskScore?.level === 'high' ? 'text-orange-400' :
                    riskScore?.level === 'medium' ? 'text-yellow-400' :
                    'text-green-400'
                  }`} />
                </div>
                <span className="text-slate-400 text-sm font-medium">Risk Score</span>
              </div>
              <p className={`text-4xl font-bold ${
                riskScore?.level === 'critical' ? 'text-red-400' :
                riskScore?.level === 'high' ? 'text-orange-400' :
                riskScore?.level === 'medium' ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {riskScore?.score ?? '--'}
              </p>
              <p className="text-xs text-slate-500 mt-2 group-hover:text-purple-400 transition-colors">
                View predictive analytics
              </p>
            </Link>
          </div>

          {/* Incidents List */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Recent Incidents</h2>
              <p className="text-sm text-slate-500 mt-1">Click on any incident to view AI analysis</p>
            </div>
            <span className="text-sm text-slate-500 bg-slate-800/50 px-4 py-2 rounded-lg">
              {incidents.length} incidents
            </span>
          </div>

          <div className="space-y-4">
            {incidents.map((incident, index) => {
              const IconComponent = incidentTypeIcons[incident.incident_type] || Activity;
              
              return (
                <Link
                  key={incident.incident_id}
                  href={`/incidents/${incident.incident_id}`}
                  className="block group"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className={`bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-blue-500/50 hover:bg-slate-900/70 transition-all duration-300 ${severityGlow[incident.severity as keyof typeof severityGlow]} hover:scale-[1.01]`}>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3 flex-wrap">
                          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${severityColors[incident.severity as keyof typeof severityColors]}`}>
                            {incident.severity}
                          </span>
                          <StatusBadge status={incident.status} size="sm" showIcon={true} />
                          <span className="text-slate-500 text-sm font-mono">
                            {incident.incident_id}
                          </span>
                          <span className="text-slate-600">•</span>
                          <div className="flex items-center gap-2">
                            <IconComponent className="h-4 w-4 text-slate-500" />
                            <span className="text-slate-400 text-sm">
                              {incidentTypeLabels[incident.incident_type] || incident.incident_type}
                            </span>
                          </div>
                        </div>
                        <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-blue-400 transition-colors">
                          {incident.title}
                        </h3>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => handlePlaySummary(incident.incident_id, e)}
                          disabled={playingIncidentId === incident.incident_id}
                          className="p-2 hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
                          title="Listen to summary"
                        >
                          {playingIncidentId === incident.incident_id ? (
                            <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                          ) : (
                            <Volume2 className="h-5 w-5 text-slate-500 hover:text-blue-400" />
                          )}
                        </button>
                        <ChevronRight className="h-6 w-6 text-slate-600 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${isIncidentActive(incident.status) ? 'bg-blue-500/20' : 'bg-slate-800/50'}`}>
                          <Clock className={`h-4 w-4 ${isIncidentActive(incident.status) ? 'text-blue-400 animate-pulse' : 'text-slate-400'}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <p className="text-slate-500 text-xs">Duration</p>
                            {isIncidentActive(incident.status) && (
                              <span className="px-1 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] rounded font-medium animate-pulse">LIVE</span>
                            )}
                          </div>
                          <p className={`font-semibold ${isIncidentActive(incident.status) ? 'text-blue-400' : 'text-white'}`}>
                            {liveDurations[incident.incident_id]
                              ? `${liveDurations[incident.incident_id].hours}h ${liveDurations[incident.incident_id].minutes}m`
                              : formatDuration(incident.duration_minutes)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800/50 rounded-lg">
                          <Activity className="h-4 w-4 text-slate-400" />
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Services</p>
                          <p className="text-white font-semibold">{incident.services_affected.length}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800/50 rounded-lg">
                          <DollarSign className="h-4 w-4 text-slate-400" />
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Cost</p>
                          <p className="text-white font-semibold">{incident.estimated_cost}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800/50 rounded-lg">
                          <Users className="h-4 w-4 text-slate-400" />
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Impact</p>
                          <p className="text-white font-semibold">{incident.users_impacted.split('+')[0]}+</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800/50 rounded-lg">
                          <Clock className="h-4 w-4 text-slate-400" />
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Started</p>
                          <p className="text-white font-semibold text-xs">{formatDate(incident.start_time)}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>

          {/* Footer hint */}
          <div className="mt-8 text-center">
            <p className="text-slate-500 text-sm">
              💡 Click any incident to view detailed AI analysis powered by Gemini 3
            </p>
          </div>
        </main>
      </div>
    </>
  );
}
