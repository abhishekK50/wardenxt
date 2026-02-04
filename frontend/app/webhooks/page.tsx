'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Send, CheckCircle, XCircle, AlertCircle, ArrowLeft, Code } from 'lucide-react';

const samplePayloads = {
  pagerduty: {
    event_type: 'incident.triggered',
    incident: {
      id: 'PD12345',
      title: 'High memory usage on prod-db-01',
      urgency: 'high',
      status: 'triggered',
      service: {
        name: 'Database Cluster'
      },
      created_at: new Date().toISOString()
    }
  },
  slack: {
    text: 'ALERT: API response time >5s on checkout service',
    channel: 'incidents',
    timestamp: Math.floor(Date.now() / 1000).toString(),
    user: 'U12345'
  },
  generic: {
    alert_name: 'CPU Threshold Exceeded',
    severity: 'critical',
    host: 'web-server-03',
    message: 'CPU usage at 95% for 5 minutes'
  }
};

type WebhookType = 'pagerduty' | 'slack' | 'generic';

export default function WebhookTestPage() {
  const [webhookType, setWebhookType] = useState<WebhookType>('pagerduty');
  const [payload, setPayload] = useState(JSON.stringify(samplePayloads.pagerduty, null, 2));
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ success: boolean; data?: any; error?: string } | null>(null);
  const router = useRouter();

  const handleWebhookTypeChange = (type: WebhookType) => {
    setWebhookType(type);
    setPayload(JSON.stringify(samplePayloads[type], null, 2));
    setResult(null);
  };

  const sendWebhook = async () => {
    setSending(true);
    setResult(null);

    try {
      // Parse JSON payload
      const parsedPayload = JSON.parse(payload);

      // Determine endpoint - use relative URL to avoid CORS
      const endpoint = `/api/webhooks/${webhookType}`;

      // Send webhook directly to backend (bypasses Next.js - may have CORS issues)
      // Use full URL with credentials
      const response = await fetch(`http://localhost:8001${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(parsedPayload),
        mode: 'cors',
        credentials: 'omit', // No credentials needed for webhooks
      });

      const data = await response.json();

      if (response.ok) {
        setResult({ success: true, data });
      } else {
        setResult({ success: false, error: data.detail || 'Failed to send webhook' });
      }
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <button
            onClick={() => router.push('/incidents')}
            className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Dashboard
          </button>
          <div>
            <h1 className="text-3xl font-bold mb-1">
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Webhook Testing
              </span>
            </h1>
            <p className="text-slate-400">
              Test webhook ingestion from PagerDuty, Slack, or generic sources
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Configuration */}
          <div className="space-y-6">
            {/* Webhook Type Selector */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Code className="h-5 w-5 text-blue-400" />
                Webhook Type
              </h2>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => handleWebhookTypeChange('pagerduty')}
                  className={`px-4 py-3 rounded-lg font-medium transition-all ${
                    webhookType === 'pagerduty'
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  PagerDuty
                </button>
                <button
                  onClick={() => handleWebhookTypeChange('slack')}
                  className={`px-4 py-3 rounded-lg font-medium transition-all ${
                    webhookType === 'slack'
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Slack
                </button>
                <button
                  onClick={() => handleWebhookTypeChange('generic')}
                  className={`px-4 py-3 rounded-lg font-medium transition-all ${
                    webhookType === 'generic'
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  Generic
                </button>
              </div>
            </div>

            {/* Payload Editor */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h2 className="text-xl font-semibold text-white mb-4">JSON Payload</h2>
              <textarea
                value={payload}
                onChange={(e) => setPayload(e.target.value)}
                className="w-full h-96 bg-slate-950 text-slate-300 font-mono text-sm p-4 rounded-lg border border-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none resize-none"
                placeholder="Enter JSON payload..."
                spellCheck={false}
              />
            </div>

            {/* Send Button */}
            <button
              onClick={sendWebhook}
              disabled={sending}
              className="w-full px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50"
            >
              {sending ? (
                <>
                  <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-5 w-5" />
                  Send Test Webhook
                </>
              )}
            </button>
          </div>

          {/* Right Column - Response */}
          <div className="space-y-6">
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h2 className="text-xl font-semibold text-white mb-4">Response</h2>

              {result ? (
                <div className="space-y-4">
                  {/* Status */}
                  <div
                    className={`flex items-center gap-3 p-4 rounded-lg ${
                      result.success
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-red-500/10 border border-red-500/30'
                    }`}
                  >
                    {result.success ? (
                      <>
                        <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
                        <div>
                          <p className="text-green-500 font-semibold">Success!</p>
                          <p className="text-sm text-green-400/80">
                            Webhook processed successfully
                          </p>
                        </div>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-6 w-6 text-red-500 flex-shrink-0" />
                        <div>
                          <p className="text-red-500 font-semibold">Failed</p>
                          <p className="text-sm text-red-400/80">{result.error}</p>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Response Data */}
                  {result.success && result.data && (
                    <div className="space-y-4">
                      <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                        <h3 className="text-sm font-semibold text-slate-400 mb-2">
                          Response Details
                        </h3>
                        <pre className="text-sm text-slate-300 font-mono overflow-x-auto">
                          {JSON.stringify(result.data, null, 2)}
                        </pre>
                      </div>

                      {/* Quick Actions */}
                      {result.data.incident_id && (
                        <div className="space-y-2">
                          <button
                            onClick={() => router.push(`/incidents/${result.data.incident_id}`)}
                            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                          >
                            <AlertCircle className="h-5 w-5" />
                            View Incident {result.data.incident_id}
                          </button>
                          <p className="text-sm text-slate-500 text-center">
                            Incident created with severity: {result.data.severity}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Send a webhook to see the response</p>
                </div>
              )}
            </div>

            {/* Endpoint Info */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h2 className="text-xl font-semibold text-white mb-4">Endpoint Info</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-slate-400">Endpoint URL</label>
                  <code className="block mt-1 px-3 py-2 bg-slate-950 text-blue-400 text-sm rounded border border-slate-800 font-mono">
                    POST /api/webhooks/{webhookType}
                  </code>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Content-Type</label>
                  <code className="block mt-1 px-3 py-2 bg-slate-950 text-slate-300 text-sm rounded border border-slate-800 font-mono">
                    application/json
                  </code>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Authentication</label>
                  <code className="block mt-1 px-3 py-2 bg-slate-950 text-slate-300 text-sm rounded border border-slate-800 font-mono">
                    None (public endpoint)
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Documentation */}
        <div className="mt-8 bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
          <h2 className="text-xl font-semibold text-white mb-4">Integration Guide</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-slate-400 mb-4">
              Configure your monitoring tools to send webhooks to WardenXT for automatic incident ingestion:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800">
                <h3 className="text-white font-semibold mb-2">PagerDuty</h3>
                <p className="text-sm text-slate-400">
                  Configure a webhook extension to send <code className="text-blue-400">incident.triggered</code> events to the PagerDuty endpoint.
                </p>
              </div>
              <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800">
                <h3 className="text-white font-semibold mb-2">Slack</h3>
                <p className="text-sm text-slate-400">
                  Set up an outgoing webhook or slash command to forward alerts to the Slack endpoint.
                </p>
              </div>
              <div className="bg-slate-950/50 p-4 rounded-lg border border-slate-800">
                <h3 className="text-white font-semibold mb-2">Generic</h3>
                <p className="text-sm text-slate-400">
                  Use the generic endpoint for any monitoring tool that can send JSON webhooks.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
