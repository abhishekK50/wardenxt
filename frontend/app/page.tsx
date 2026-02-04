'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  Zap,
  Shield,
  TrendingUp,
  Mic,
  FileText,
  AlertCircle,
  ArrowRight,
  Brain,
  Clock,
  DollarSign,
  Activity
} from 'lucide-react';
import { api, RiskScore } from '@/lib/api';

export default function HomePage() {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [incidentCount, setIncidentCount] = useState<number | null>(null);

  useEffect(() => {
    // Fetch live stats
    const fetchStats = async () => {
      try {
        const [risk, incidents] = await Promise.all([
          api.getRiskScore().catch(() => null),
          api.listIncidents().catch(() => ({ incidents: [] }))
        ]);
        setRiskScore(risk);
        setIncidentCount(incidents.incidents?.length || 0);
      } catch (e) {
        // Silently fail - stats are optional
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 py-16 lg:py-24">
        <div className="text-center mb-16">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full mb-8">
            <Sparkles className="h-4 w-4 text-blue-400" />
            <span className="text-sm text-blue-400 font-medium">Google Gemini 3 Hackathon Project</span>
          </div>

          {/* Title */}
          <h1 className="text-5xl lg:text-7xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-green-400 bg-clip-text text-transparent">
              WardenXT
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-2xl lg:text-3xl text-slate-300 mb-4">
            AI-Powered Incident Commander
          </p>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto mb-8">
            From reactive firefighting to proactive prevention. WardenXT uses Google Gemini 3
            to analyze thousands of logs, predict future incidents, and generate executable
            remediation plans in seconds.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link
              href="/incidents"
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold text-lg hover:scale-105 transition-transform shadow-lg shadow-blue-500/25"
            >
              <AlertCircle className="h-5 w-5" />
              View Incidents
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold text-lg transition-colors border border-slate-700"
            >
              <Brain className="h-5 w-5 text-purple-400" />
              Predictive Dashboard
            </Link>
          </div>

          {/* Live Stats */}
          {(riskScore || incidentCount !== null) && (
            <div className="flex flex-wrap justify-center gap-6 mb-8">
              {riskScore && (
                <div className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
                  <Shield className={`h-5 w-5 ${
                    riskScore.level === 'critical' ? 'text-red-400' :
                    riskScore.level === 'high' ? 'text-orange-400' :
                    riskScore.level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                  }`} />
                  <span className="text-slate-400">Live Risk Score:</span>
                  <span className={`font-bold ${
                    riskScore.level === 'critical' ? 'text-red-400' :
                    riskScore.level === 'high' ? 'text-orange-400' :
                    riskScore.level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                  }`}>{riskScore.score}</span>
                </div>
              )}
              {incidentCount !== null && (
                <div className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
                  <Activity className="h-5 w-5 text-blue-400" />
                  <span className="text-slate-400">Incidents Tracked:</span>
                  <span className="text-white font-bold">{incidentCount}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-20">
          <FeatureCard
            icon={<Sparkles className="h-8 w-8 text-blue-400" />}
            title="AI Root Cause Analysis"
            description="Gemini 3 analyzes thousands of logs, metrics, and events to identify root causes in seconds, not hours."
            color="blue"
          />
          <FeatureCard
            icon={<Mic className="h-8 w-8 text-cyan-400" />}
            title="Voice AI Commander"
            description="Ask questions naturally: 'What's the most critical incident?' Get spoken responses with full context."
            color="cyan"
          />
          <FeatureCard
            icon={<FileText className="h-8 w-8 text-green-400" />}
            title="Auto Runbook Generation"
            description="One-click generation of executable bash, kubectl, and SQL remediation scripts with rollback instructions."
            color="green"
          />
          <FeatureCard
            icon={<TrendingUp className="h-8 w-8 text-purple-400" />}
            title="Predictive Analytics"
            description="Forecast incidents 24-72 hours before they occur using historical pattern analysis and ML."
            color="purple"
          />
          <FeatureCard
            icon={<Zap className="h-8 w-8 text-yellow-400" />}
            title="Real-Time Ingestion"
            description="Webhook integration with PagerDuty, ServiceNow, Slack, and custom monitoring tools."
            color="yellow"
          />
          <FeatureCard
            icon={<Shield className="h-8 w-8 text-red-400" />}
            title="Risk Scoring"
            description="Real-time 0-100 risk score with contributing factors, trend analysis, and what-if simulation."
            color="red"
          />
        </div>

        {/* Stats Section */}
        <div className="grid md:grid-cols-3 gap-6 mb-20">
          <StatCard
            icon={<Clock className="h-6 w-6 text-blue-400" />}
            value="<5s"
            label="AI Analysis Response Time"
            description="From log ingestion to root cause identification"
          />
          <StatCard
            icon={<TrendingUp className="h-6 w-6 text-green-400" />}
            value="78%"
            label="Incident Prediction Accuracy"
            description="Based on historical pattern matching"
          />
          <StatCard
            icon={<DollarSign className="h-6 w-6 text-purple-400" />}
            value="$5M+"
            label="Potential Cost Savings"
            description="Through faster MTTR and prevention"
          />
        </div>

        {/* How It Works */}
        <div className="mb-20">
          <h2 className="text-3xl font-bold text-white text-center mb-12">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <StepCard
              step={1}
              title="Ingest"
              description="Receive incidents via webhooks from your monitoring tools"
            />
            <StepCard
              step={2}
              title="Analyze"
              description="Gemini 3 processes logs, metrics, and timelines"
            />
            <StepCard
              step={3}
              title="Generate"
              description="Create runbooks with executable remediation commands"
            />
            <StepCard
              step={4}
              title="Prevent"
              description="Predict future incidents and take proactive action"
            />
          </div>
        </div>

        {/* Powered By */}
        <div className="text-center">
          <p className="text-slate-500 text-sm mb-3">Powered by</p>
          <p className="text-3xl font-semibold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            Google Gemini 3 Flash
          </p>
          <p className="text-slate-400 mt-4 max-w-xl mx-auto">
            Built for the Google Gemini 3 Hackathon. Showcasing AI-powered incident management
            with voice interaction, predictive analytics, and automated runbook generation.
          </p>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  color
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
}) {
  const borderColors: Record<string, string> = {
    blue: 'hover:border-blue-500/50',
    cyan: 'hover:border-cyan-500/50',
    green: 'hover:border-green-500/50',
    purple: 'hover:border-purple-500/50',
    yellow: 'hover:border-yellow-500/50',
    red: 'hover:border-red-500/50',
  };

  return (
    <div className={`bg-slate-900/50 border border-slate-800 rounded-xl p-6 ${borderColors[color]} transition-all hover:shadow-lg hover:-translate-y-1`}>
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-slate-400">{description}</p>
    </div>
  );
}

function StatCard({
  icon,
  value,
  label,
  description
}: {
  icon: React.ReactNode;
  value: string;
  label: string;
  description: string;
}) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 text-center">
      <div className="flex justify-center mb-4">{icon}</div>
      <p className="text-4xl font-bold text-white mb-2">{value}</p>
      <p className="text-slate-300 font-medium mb-1">{label}</p>
      <p className="text-slate-500 text-sm">{description}</p>
    </div>
  );
}

function StepCard({
  step,
  title,
  description
}: {
  step: number;
  title: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
        {step}
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-slate-400 text-sm">{description}</p>
    </div>
  );
}
