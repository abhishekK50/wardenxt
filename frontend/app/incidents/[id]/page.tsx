'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Clock, DollarSign, Users, AlertTriangle, CheckCircle, Sparkles, Loader2, Webhook, ChevronDown, ChevronUp, Volume2, VolumeX, Wrench } from 'lucide-react';
import { useAPI } from '@/lib/hooks/useAPI';
import { useToast } from '@/app/components/ErrorToast';
import StatusBadge, { type IncidentStatus } from '@/app/components/StatusBadge';
import StatusUpdateDropdown from '@/app/components/StatusUpdateDropdown';
import StatusHistory from '@/app/components/StatusHistory';
import AgentReasoningView from '@/app/components/AgentReasoningView';
import MetricsDashboard from '@/app/components/MetricsDashboard';
import RCADocumentGenerator from '@/app/components/RCADocumentGenerator';
import RunbookPanel from '@/app/components/RunbookPanel';
import CommandExecutionModal from '@/app/components/CommandExecutionModal';
import ExecutionHistory from '@/app/components/ExecutionHistory';
import { exportRunbookAsMarkdown } from '@/app/components/RunbookExport';
import type { Runbook, RunbookCommand, ExecutionResult } from '@/lib/api';


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
  start_time?: string;
  status?: string;
}

// Helper to calculate live duration from start time
function calculateLiveDuration(startTime: string | undefined): { hours: number; minutes: number; seconds: number; totalMinutes: number } {
  if (!startTime) {
    return { hours: 0, minutes: 0, seconds: 0, totalMinutes: 0 };
  }

  const start = new Date(startTime).getTime();
  const now = Date.now();
  const diffMs = Math.max(0, now - start);

  const totalSeconds = Math.floor(diffMs / 1000);
  const totalMinutes = Math.floor(totalSeconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  const seconds = totalSeconds % 60;

  return { hours, minutes, seconds, totalMinutes };
}

// Check if incident is active (not resolved/closed)
function isIncidentActive(status: string | undefined): boolean {
  if (!status) return true;
  const resolvedStatuses = ['RESOLVED', 'CLOSED'];
  return !resolvedStatuses.includes(status.toUpperCase());
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
  const api = useAPI();
  const { showToast, ToastContainer } = useToast();
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<IncidentStatus>('DETECTED');
  const [statusHistoryKey, setStatusHistoryKey] = useState(0);
  const [webhookMetadata, setWebhookMetadata] = useState<any>(null);
  const [showRawPayload, setShowRawPayload] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [speechUtterance, setSpeechUtterance] = useState<SpeechSynthesisUtterance | null>(null);
  const [liveDuration, setLiveDuration] = useState({ hours: 0, minutes: 0, seconds: 0, totalMinutes: 0 });

  // Runbook state
  const [runbook, setRunbook] = useState<Runbook | null>(null);
  const [generatingRunbook, setGeneratingRunbook] = useState(false);
  const [executedSteps, setExecutedSteps] = useState<Set<number>>(new Set());
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [selectedCommand, setSelectedCommand] = useState<{
    command: RunbookCommand;
    stepNumber: number;
    commandIndex: number;
  } | null>(null);

  useEffect(() => {
    if (params.id) {
      fetchIncidentData(params.id as string);
      fetchCurrentStatus(params.id as string);
      fetchWebhookMetadata(params.id as string);
    }
  }, [params.id]);

  // Real-time duration updates for active incidents
  useEffect(() => {
    if (!incident?.start_time) return;

    // Check if incident is still active
    const isActive = isIncidentActive(currentStatus);

    if (!isActive) {
      // For resolved incidents, show static duration
      setLiveDuration({
        hours: Math.floor(incident.duration_minutes / 60),
        minutes: incident.duration_minutes % 60,
        seconds: 0,
        totalMinutes: incident.duration_minutes
      });
      return;
    }

    // Initial calculation
    setLiveDuration(calculateLiveDuration(incident.start_time));

    // Update every second for real-time display
    const interval = setInterval(() => {
      setLiveDuration(calculateLiveDuration(incident.start_time));
    }, 1000);

    return () => clearInterval(interval);
  }, [incident?.start_time, incident?.duration_minutes, currentStatus]);

  const fetchCurrentStatus = async (id: string) => {
    try {
      const data = await api.getIncidentStatus(id);
      setCurrentStatus(data.current_status as IncidentStatus);
    } catch (error) {
      // Status not found is expected for incidents without status history
      // Only log in development for debugging
      if (process.env.NODE_ENV === 'development') {
        console.log('Status not available for incident:', id);
      }
    }
  };

  const fetchWebhookMetadata = async (id: string) => {
    try {
      const data = await api.getWebhookIncident(id);
      if (data) {
        setWebhookMetadata(data);
      }
    } catch {
      // Not a webhook incident - that's expected for most incidents
    }
  };

  const handleStatusChange = (newStatus: IncidentStatus) => {
    setCurrentStatus(newStatus);
    setStatusHistoryKey(prev => prev + 1);
  };

  const fetchIncidentData = async (id: string) => {
    try {
      setLoading(true);

      // Fetch summary
      const summaryData = await api.getIncidentSummary(id);
      setIncident(summaryData as any);

      // Fetch timeline
      const timelineData = await api.getIncidentTimeline(id);
      setTimeline(Array.isArray(timelineData) ? timelineData : []);

      // Fetch metrics
      const metricsData = await api.getIncidentMetrics(id, 50);
      setMetrics(metricsData.map((m: any, i: number) => ({
        index: i,
        cpu: m.metrics.cpu_percent,
        memory: m.metrics.memory_mb,
        requests: m.metrics.requests_per_sec,
        errors: m.metrics.error_rate * 100,
        time: new Date(m.timestamp).toLocaleTimeString()
      })));

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load incident data';
      console.error('Error:', err);
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };


  const runAnalysis = async () => {
    if (!incident) return;
    setAnalyzing(true);
    try {
      const data = await api.analyzeIncident(incident.incident_id);
      setAnalysis(data);
      showToast('Analysis completed successfully', 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze incident';
      console.error(err);
      showToast(errorMessage, 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePlaySummary = async () => {
    if (!incident) return;

    // Stop current speech if playing
    if (speechUtterance) {
      window.speechSynthesis.cancel();
      setIsPlayingAudio(false);
      setSpeechUtterance(null);
      return;
    }

    try {
      setIsPlayingAudio(true);

      // Get summary text from backend
      const summaryData = await api.getIncidentAudioSummary(incident.incident_id);

      // Check if browser supports speech synthesis
      if (!('speechSynthesis' in window)) {
        showToast('Your browser does not support text-to-speech', 'error');
        setIsPlayingAudio(false);
        return;
      }

      // Create and configure utterance
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
        setIsPlayingAudio(false);
        setSpeechUtterance(null);
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        showToast('Failed to play audio summary', 'error');
        setIsPlayingAudio(false);
        setSpeechUtterance(null);
      };

      setSpeechUtterance(utterance);
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load summary';
      console.error(err);
      showToast(errorMessage, 'error');
      setIsPlayingAudio(false);
      setSpeechUtterance(null);
    }
  };

  const generateRunbook = async () => {
    if (!incident) return;

    setGeneratingRunbook(true);
    try {
      const generatedRunbook = await api.generateRunbook(incident.incident_id);
      setRunbook(generatedRunbook);
      showToast('Runbook generated successfully', 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate runbook';
      console.error(err);
      showToast(errorMessage, 'error');
    } finally {
      setGeneratingRunbook(false);
    }
  };

  const handleExecuteCommand = (stepNumber: number, commandIndex: number, command: RunbookCommand) => {
    setSelectedCommand({ command, stepNumber, commandIndex });
    setShowExecutionModal(true);
  };

  const executeCommand = async (dryRun: boolean, confirmationText?: string): Promise<ExecutionResult> => {
    if (!selectedCommand || !incident) {
      throw new Error('No command selected');
    }

    const result = await api.executeRunbookStep(incident.incident_id, {
      step_number: selectedCommand.stepNumber,
      command_index: selectedCommand.commandIndex,
      dry_run: dryRun,
      confirmation_text: confirmationText,
      executed_by: 'user'
    });

    // Mark step as executed if successful and not dry-run
    if (result.success && !dryRun) {
      setExecutedSteps(prev => new Set(prev).add(selectedCommand.stepNumber));
    }

    return result;
  };

  const handleExportRunbook = () => {
    if (runbook) {
      exportRunbookAsMarkdown(runbook);
      showToast('Runbook exported successfully', 'success');
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
    <>
      <ToastContainer />
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <button onClick={() => router.push('/incidents')} className="flex items-center gap-2 text-slate-400 hover:text-white mb-4">
            <ArrowLeft className="h-5 w-5" /> Back
          </button>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${severityColors[incident.severity as keyof typeof severityColors]}`}>
                  {incident.severity}
                </span>
                <StatusBadge status={currentStatus} size="md" />
                {webhookMetadata && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/50 flex items-center gap-1.5">
                    <Webhook className="h-3 w-3" />
                    {webhookMetadata.source === 'pagerduty' && 'PagerDuty'}
                    {webhookMetadata.source === 'slack' && 'Slack'}
                    {webhookMetadata.source === 'generic' && 'Generic Webhook'}
                    {webhookMetadata.auto_analyzed && (
                      <span className="ml-1 px-1.5 py-0.5 bg-blue-500/30 text-blue-300 rounded text-xs">AI</span>
                    )}
                  </span>
                )}
                <span className="text-slate-500 font-mono text-sm">{incident.incident_id}</span>
              </div>
              <h1 className="text-3xl font-bold text-white">{incident.title}</h1>
            </div>
            
            <div className="flex items-center gap-3">
              <StatusUpdateDropdown
                incidentId={incident.incident_id}
                currentStatus={currentStatus}
                onStatusChange={handleStatusChange}
              />
              <button
                onClick={runAnalysis}
                disabled={analyzing}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin inline mr-2" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5 inline mr-2" />
                    AI Analysis
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Actions Bar */}
        <div className="mb-6 flex items-center gap-4 p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
          <span className="text-sm text-slate-400 font-medium">Quick Actions:</span>
          <button
            onClick={handlePlaySummary}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors border border-slate-700"
          >
            {isPlayingAudio ? (
              <>
                <VolumeX className="h-4 w-4 text-purple-400" />
                Stop Audio
              </>
            ) : (
              <>
                <Volume2 className="h-4 w-4 text-purple-400" />
                Listen to Summary
              </>
            )}
          </button>
          <button
            onClick={generateRunbook}
            disabled={generatingRunbook}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generatingRunbook ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-orange-400" />
                Generating...
              </>
            ) : runbook ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-400" />
                Runbook Ready
              </>
            ) : (
              <>
                <Wrench className="h-4 w-4 text-orange-400" />
                Generate Runbook
              </>
            )}
          </button>
        </div>

        {/* Webhook Source Info */}
        {webhookMetadata && (
          <div className="mb-8 bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowRawPayload(!showRawPayload)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Webhook className="h-5 w-5 text-purple-400" />
                <div className="text-left">
                  <h3 className="text-lg font-semibold text-white">
                    Webhook Source: {webhookMetadata.source === 'pagerduty' && 'PagerDuty'}
                    {webhookMetadata.source === 'slack' && 'Slack'}
                    {webhookMetadata.source === 'generic' && 'Generic Webhook'}
                  </h3>
                  <p className="text-sm text-slate-400">
                    Auto-ingested on {new Date(webhookMetadata.created_at).toLocaleString()}
                    {webhookMetadata.auto_analyzed && ' • AI analysis completed'}
                  </p>
                </div>
              </div>
              {showRawPayload ? (
                <ChevronUp className="h-5 w-5 text-slate-400" />
              ) : (
                <ChevronDown className="h-5 w-5 text-slate-400" />
              )}
            </button>

            {showRawPayload && (
              <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/50">
                <h4 className="text-sm font-semibold text-slate-400 mb-3">Raw Webhook Payload</h4>
                <pre className="text-xs text-slate-300 font-mono bg-slate-900 p-4 rounded-lg border border-slate-800 overflow-x-auto">
                  {JSON.stringify(webhookMetadata.raw_payload, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Agent Reasoning View - Real-time */}
        {analyzing && (
          <div className="mb-8">
            <AgentReasoningView incidentId={incident.incident_id} isAnalyzing={analyzing} />
          </div>
        )}

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

            {/* Root Cause with Confidence */}
            {analysis.root_cause && (
              <div className="mb-6 bg-slate-900/50 rounded-lg p-4 border border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-blue-300">Root Cause Analysis</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Confidence:</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      analysis.root_cause.confidence >= 0.9 
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : analysis.root_cause.confidence >= 0.75
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        : analysis.root_cause.confidence >= 0.5
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                      {Math.round(analysis.root_cause.confidence * 100)}%
                    </span>
                  </div>
                </div>
                <p className="text-slate-200 mb-3">{analysis.root_cause.primary_cause}</p>
                
                {/* Evidence */}
                {analysis.root_cause.evidence && analysis.root_cause.evidence.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-slate-400 mb-2">Evidence:</h4>
                    <ul className="space-y-1">
                      {analysis.root_cause.evidence.map((evidence: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0 mt-0.5" />
                          <span>{evidence}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Contributing Factors */}
                {analysis.root_cause.contributing_factors && analysis.root_cause.contributing_factors.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-slate-400 mb-2">Contributing Factors:</h4>
                    <ul className="space-y-1">
                      {analysis.root_cause.contributing_factors.map((factor: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <span className="text-orange-400">•</span>
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

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
          <div className={`bg-slate-900/50 border rounded-lg p-6 ${isIncidentActive(currentStatus) ? 'border-blue-500/50' : 'border-slate-800'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Clock className={`h-5 w-5 ${isIncidentActive(currentStatus) ? 'text-blue-400 animate-pulse' : 'text-blue-400'}`} />
              {isIncidentActive(currentStatus) && (
                <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full font-medium animate-pulse">LIVE</span>
              )}
            </div>
            <p className="text-slate-400 text-sm">Duration</p>
            <p className={`text-2xl font-bold ${isIncidentActive(currentStatus) ? 'text-blue-400' : 'text-white'}`}>
              {liveDuration.hours}h {liveDuration.minutes}m
              {isIncidentActive(currentStatus) && (
                <span className="text-lg text-blue-300"> {liveDuration.seconds.toString().padStart(2, '0')}s</span>
              )}
            </p>
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

          </div>
        </div>

        {/* Status History */}
        <div className="mb-8 bg-slate-900/50 border border-slate-800 rounded-lg p-6">
          <StatusHistory key={statusHistoryKey} incidentId={incident.incident_id} />
        </div>

        {/* Enhanced Metrics Dashboard */}
        <div className="mb-8">
          <MetricsDashboard metrics={metrics} />
        </div>

        {/* RCA Document Generator */}
        {analysis && (
          <div className="mb-8">
            <RCADocumentGenerator
              incident={{
                incident_id: incident.incident_id,
                title: incident.title,
                severity: incident.severity,
                duration_minutes: incident.duration_minutes,
                services_affected: incident.services_affected,
                root_cause: {
                  primary: incident.root_cause.primary,
                  secondary: incident.root_cause.secondary,
                },
                mitigation_steps: incident.mitigation_steps,
                lessons_learned: incident.lessons_learned,
              }}
              analysis={analysis}
            />
          </div>
        )}

        {/* Auto-Generated Runbook */}
        {runbook && (
          <div className="mb-8">
            <RunbookPanel
              runbook={runbook}
              onExecuteCommand={handleExecuteCommand}
              onExport={handleExportRunbook}
              executedSteps={executedSteps}
            />
          </div>
        )}

        {/* Execution History */}
        {runbook && (
          <div className="mb-8">
            <ExecutionHistory incidentId={incident.incident_id} />
          </div>
        )}
      </main>
    </div>

    {/* Command Execution Modal */}
    <CommandExecutionModal
      isOpen={showExecutionModal}
      onClose={() => {
        setShowExecutionModal(false);
        setSelectedCommand(null);
      }}
      command={selectedCommand?.command || null}
      stepNumber={selectedCommand?.stepNumber || 0}
      commandIndex={selectedCommand?.commandIndex || 0}
      onExecute={executeCommand}
    />
    </>
  );
}