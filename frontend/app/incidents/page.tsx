'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, Clock, DollarSign, Users, TrendingUp, ChevronRight, Activity, Zap } from 'lucide-react';
import { useAPI } from '@/lib/hooks/useAPI';
import { useToast } from '@/app/components/ErrorToast';
import StatusBadge, { IncidentStatus } from '@/app/components/StatusBadge';

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
  const api = useAPI();
  const { showToast, ToastContainer } = useToast();

  useEffect(() => {
    fetchIncidents();
  }, []);

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
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-500">Powered by</span>
                <span className="text-lg font-semibold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  Gemini 3 Flash Preview
                </span>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
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
                      <ChevronRight className="h-6 w-6 text-slate-600 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" />
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800/50 rounded-lg">
                          <Clock className="h-4 w-4 text-slate-400" />
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs">Duration</p>
                          <p className="text-white font-semibold">{formatDuration(incident.duration_minutes)}</p>
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
