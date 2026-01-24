'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Clock, DollarSign, Users, AlertTriangle, CheckCircle, Sparkles, Loader2 } from 'lucide-react';


interface IncidentDetail {
  incident_id: string;
  title: string;
  severity: string;
  duration_minutes: number;
  services_affected: string[];
  estimated_cost: string;
  users_impacted: string;
  root_cause: any;
  mitigation_steps: string[];
  lessons_learned?: string[];
}

const severityColors = {
  P0: 'bg-red-500/10 text-red-500 border-red-500/20',
  P1: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  P2: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  P3: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
};

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchIncidentData(params.id as string);
    }
  }, [params.id]);

  const fetchIncidentData = async (id: string) => {
    try {
      setLoading(true);
      
      // Fetch summary
      const summaryRes = await fetch(`http://localhost:8000/api/incidents/${id}/summary`);
      const summaryData = await summaryRes.json();
      setIncident(summaryData);
      
      // Fetch timeline
      const timelineRes = await fetch(`http://localhost:8000/api/incidents/${id}/timeline`);
      const timelineData = await timelineRes.json();
      setTimeline(timelineData || []);

      const metricsRes = await fetch(`http://localhost:8000/api/incidents/${id}/metrics?limit=50`);
const metricsData = await metricsRes.json();
setMetrics(metricsData.map((m: any, i: number) => ({
  index: i,
  cpu: m.metrics.cpu_percent,
  memory: m.metrics.memory_mb,
  requests: m.metrics.requests_per_sec,
  errors: m.metrics.error_rate * 100,
  time: new Date(m.timestamp).toLocaleTimeString()
})));
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };


  const runAnalysis = async () => {
    if (!incident) return;
    setAnalyzing(true);
    try {
      const res = await fetch(`http://localhost:8000/api/analysis/${incident.incident_id}/analyze`, { method: 'POST' });
      const data = await res.json();
      setAnalysis(data);
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <button onClick={() => router.push('/incidents')} className="px-6 py-3 bg-blue-600 text-white rounded-lg">
          Back to Incidents
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <button onClick={() => router.push('/incidents')} className="flex items-center gap-2 text-slate-400 hover:text-white mb-4">
            <ArrowLeft className="h-5 w-5" /> Back
          </button>
          <div className="flex items-center gap-3 mb-2">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${severityColors[incident.severity as keyof typeof severityColors]}`}>
              {incident.severity}
            </span>
            <span className="text-slate-500">{incident.incident_id}</span>
          </div>
          <h1 className="text-3xl font-bold text-white">{incident.title}</h1>
          <button onClick={runAnalysis} disabled={analyzing} className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold">
  {analyzing ? <><Loader2 className="h-5 w-5 animate-spin inline mr-2" />Analyzing...</> : <><Sparkles className="h-5 w-5 inline mr-2" />AI Analysis</>}
</button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">


        {/* AI Analysis Results */}
        {analysis && (
          <div className="mb-8 bg-gradient-to-br from-blue-900/20 to-cyan-900/20 border border-blue-500/30 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Sparkles className="h-6 w-6 text-blue-400" />
              <h2 className="text-2xl font-bold text-white">Gemini 3 Analysis</h2>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-blue-300 mb-2">Executive Summary</h3>
              <p className="text-slate-200 leading-relaxed">{analysis.executive_summary}</p>
            </div>

            {analysis.recommended_actions && (
              <div>
                <h3 className="text-lg font-semibold text-blue-300 mb-3">Recommended Actions</h3>
                <div className="space-y-2">
                  {analysis.recommended_actions.map((rec: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded font-semibold">
                        {rec.priority}
                      </span>
                      <p className="text-slate-200 text-sm flex-1">{rec.action}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <Clock className="h-5 w-5 text-blue-400 mb-2" />
            <p className="text-slate-400 text-sm">Duration</p>
            <p className="text-2xl font-bold text-white">{Math.floor(incident.duration_minutes/60)}h {incident.duration_minutes%60}m</p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <AlertTriangle className="h-5 w-5 text-orange-400 mb-2" />
            <p className="text-slate-400 text-sm">Services</p>
            <p className="text-2xl font-bold text-white">{incident.services_affected.length}</p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <DollarSign className="h-5 w-5 text-red-400 mb-2" />
            <p className="text-slate-400 text-sm">Cost</p>
            <p className="text-2xl font-bold text-white">{incident.estimated_cost}</p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <Users className="h-5 w-5 text-yellow-400 mb-2" />
            <p className="text-slate-400 text-sm">Impact</p>
            <p className="text-2xl font-bold text-white">{incident.users_impacted.split('+')[0]}+</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Timeline */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-6">Timeline</h2>
            {timeline.length > 0 ? (
              <div className="space-y-6">
                {timeline.map((event, i) => (
                  <div key={i} className="relative pl-6 border-l-2 border-slate-700">
                    <div className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-blue-500 border-2 border-slate-900"></div>
                    <span className="text-blue-400 font-mono text-sm">{event.time}</span>
                    <h3 className="text-white font-semibold">{event.event}</h3>
                    <p className="text-slate-400 text-sm">{event.impact}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500">Loading timeline...</p>
            )}
          </div>

          <div className="space-y-6">
            {/* Root Cause */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Root Cause</h2>
              <div className="space-y-3">
                <div>
                  <span className="text-red-400 font-semibold">Primary:</span>
                  <p className="text-slate-300 mt-1">{incident.root_cause.primary}</p>
                </div>
                {incident.root_cause.secondary && (
                  <div>
                    <span className="text-orange-400 font-semibold">Secondary:</span>
                    <p className="text-slate-300 mt-1">{incident.root_cause.secondary}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Mitigation */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Mitigation Steps</h2>
              <div className="space-y-2">
                {incident.mitigation_steps.map((step, i) => (
                  <div key={i} className="flex gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <p className="text-slate-300 text-sm">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Services */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Affected Services</h2>
              <div className="flex flex-wrap gap-2">
                {incident.services_affected.map((service, i) => (
                  <span key={i} className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-sm">
                    {service}
                  </span>
                ))}
              </div>
            </div>

            {/* Metrics Chart */}
<div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-lg p-6">
  <h2 className="text-xl font-bold text-white mb-4">System Metrics</h2>
  <div className="h-[300px]">
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={metrics}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis stroke="#64748b" />
        <YAxis stroke="#64748b" />
        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
        <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} name="CPU %" />
<Line type="monotone" dataKey="memory" stroke="#10b981" strokeWidth={2} name="Memory MB" />
<Line type="monotone" dataKey="requests" stroke="#f59e0b" strokeWidth={2} name="Requests/s" />
      </LineChart>
    </ResponsiveContainer>
  </div>
</div>
          </div>
        </div>
      </main>
    </div>
  );
}