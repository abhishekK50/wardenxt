'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, Clock, DollarSign, Users, TrendingUp, ChevronRight } from 'lucide-react';

interface Incident {
  incident_id: string;
  title: string;
  severity: string;
  incident_type: string;
  start_time: string;
  duration_minutes: number;
  services_affected: string[];
  estimated_cost: string;
  users_impacted: string;
  mttr_actual: string;
}

const severityColors = {
  P0: 'bg-red-500/10 text-red-500 border-red-500/20',
  P1: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  P2: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  P3: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
};

const incidentTypeLabels: Record<string, string> = {
  bmr_recovery: 'Hardware Failure',
  connection_pool_exhaustion: 'Resource Exhaustion',
  memory_leak: 'Memory Management',
  dns_propagation: 'Network Infrastructure',
  kubernetes_crashloop: 'Container Orchestration',
};

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/incidents/');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch incidents: ${response.statusText}`);
      }
      
      const data = await response.json();
      setIncidents(data.incidents || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching incidents:', err);
      setError(err instanceof Error ? err.message : 'Failed to load incidents');
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
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent mb-4"></div>
          <p className="text-slate-400 text-lg">Loading incidents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
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
            Make sure the backend is running at http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  const stats = {
    total: incidents.length,
    p1: incidents.filter(i => i.severity === 'P1').length,
    p2: incidents.filter(i => i.severity === 'P2').length,
    totalCost: incidents.reduce((sum, i) => {
      const cost = parseInt(i.estimated_cost.replace(/[$,]/g, ''));
      return sum + (isNaN(cost) ? 0 : cost);
    }, 0),
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">
                WardenXT
              </h1>
              <p className="text-slate-400">
                AI-Powered Incident Commander for P0/P1/P2 Critical Incidents
              </p>
            </div>
            <div className="flex items-center gap-4">
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-2">
              <AlertCircle className="h-5 w-5 text-blue-400" />
              <span className="text-slate-400 text-sm">Total Incidents</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.total}</p>
          </div>
          
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="h-5 w-5 text-orange-400" />
              <span className="text-slate-400 text-sm">Critical (P1)</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.p1}</p>
          </div>
          
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-2">
              <AlertCircle className="h-5 w-5 text-yellow-400" />
              <span className="text-slate-400 text-sm">High (P2)</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.p2}</p>
          </div>
          
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="h-5 w-5 text-red-400" />
              <span className="text-slate-400 text-sm">Total Impact</span>
            </div>
            <p className="text-3xl font-bold text-white">
              ${(stats.totalCost / 1000000).toFixed(1)}M
            </p>
          </div>
        </div>

        {/* Incidents List */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Recent Incidents</h2>
          <span className="text-sm text-slate-500">{incidents.length} incidents</span>
        </div>

        <div className="space-y-4">
          {incidents.map((incident) => (
            <Link 
              key={incident.incident_id} 
              href={`/incidents/${incident.incident_id}`}
              className="block group"
            >
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm hover:border-blue-500/50 hover:bg-slate-900/70 transition-all duration-200">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${severityColors[incident.severity as keyof typeof severityColors]}`}>
                        {incident.severity}
                      </span>
                      <span className="text-slate-500 text-sm">
                        {incident.incident_id}
                      </span>
                      <span className="text-slate-600">•</span>
                      <span className="text-slate-500 text-sm">
                        {incidentTypeLabels[incident.incident_type] || incident.incident_type}
                      </span>
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-blue-400 transition-colors">
                      {incident.title}
                    </h3>
                  </div>
                  <ChevronRight className="h-6 w-6 text-slate-600 group-hover:text-blue-400 transition-colors" />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-slate-500" />
                    <div>
                      <p className="text-slate-500">Duration</p>
                      <p className="text-white font-medium">{formatDuration(incident.duration_minutes)}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-slate-500" />
                    <div>
                      <p className="text-slate-500">Services</p>
                      <p className="text-white font-medium">{incident.services_affected.length}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-slate-500" />
                    <div>
                      <p className="text-slate-500">Cost</p>
                      <p className="text-white font-medium">{incident.estimated_cost}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-slate-500" />
                    <div>
                      <p className="text-slate-500">Impact</p>
                      <p className="text-white font-medium">{incident.users_impacted.split('+')[0]}+</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-slate-500" />
                    <div>
                      <p className="text-slate-500">Started</p>
                      <p className="text-white font-medium">{formatDate(incident.start_time)}</p>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}