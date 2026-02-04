'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { X, Volume2, VolumeX } from 'lucide-react';

interface VoiceResponse {
  transcript: string;
  response_text: string;
  audio_base64?: string;
  action_taken?: string;
  incident_ids?: string[];
  confidence: number;
}

interface VoiceResponsePopupProps {
  response: VoiceResponse;
  onClose: () => void;
  isPlaying: boolean;
}

export default function VoiceResponsePopup({ response, onClose, isPlaying }: VoiceResponsePopupProps) {
  const router = useRouter();
  const [showWaveform, setShowWaveform] = useState(false);
  const [autoDismissTimer, setAutoDismissTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Auto-dismiss after 10 seconds
    const timer = setTimeout(() => {
      onClose();
    }, 10000);

    setAutoDismissTimer(timer);

    return () => {
      if (autoDismissTimer) {
        clearTimeout(autoDismissTimer);
      }
    };
  }, []);

  useEffect(() => {
    setShowWaveform(isPlaying);
  }, [isPlaying]);

  const handleIncidentClick = (incidentId: string) => {
    router.push(`/incidents/${incidentId}`);
    onClose();
  };

  const handleClose = () => {
    if (autoDismissTimer) {
      clearTimeout(autoDismissTimer);
    }
    onClose();
  };

  return (
    <div className="fixed bottom-28 right-6 z-50 max-w-md animate-slide-in-right">
      <div className="bg-slate-900/95 border border-slate-700 rounded-lg shadow-2xl backdrop-blur-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-slate-800/50">
          <div className="flex items-center gap-2">
            {showWaveform ? (
              <Volume2 className="h-5 w-5 text-blue-400 animate-pulse" />
            ) : (
              <VolumeX className="h-5 w-5 text-slate-400" />
            )}
            <span className="text-sm font-semibold text-white">WardenXT Response</span>
          </div>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Transcript */}
          <div>
            <div className="text-xs text-slate-500 mb-1 flex items-center gap-2">
              <span>You said:</span>
              {response.confidence < 0.8 && (
                <span className="text-yellow-500">(Low confidence: {(response.confidence * 100).toFixed(0)}%)</span>
              )}
            </div>
            <p className="text-sm text-slate-300 italic">"{response.transcript}"</p>
          </div>

          {/* Response */}
          <div>
            <div className="text-xs text-blue-400 mb-1">WardenXT:</div>
            <p className="text-sm text-white">{response.response_text}</p>
          </div>

          {/* Audio Waveform Animation */}
          {showWaveform && (
            <div className="flex items-center justify-center gap-1 py-2">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-blue-500 rounded-full animate-pulse"
                  style={{
                    height: `${Math.random() * 24 + 8}px`,
                    animationDelay: `${i * 0.05}s`,
                    animationDuration: `${0.5 + Math.random() * 0.5}s`
                  }}
                />
              ))}
            </div>
          )}

          {/* Action Taken */}
          {response.action_taken && (
            <div className="bg-green-900/30 border border-green-500/30 rounded px-3 py-2">
              <div className="text-xs text-green-400 mb-1">Action Taken:</div>
              <p className="text-sm text-green-300">{response.action_taken}</p>
            </div>
          )}

          {/* Incident IDs */}
          {response.incident_ids && response.incident_ids.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-2">Related Incidents:</div>
              <div className="flex flex-wrap gap-2">
                {response.incident_ids.map((incidentId) => (
                  <button
                    key={incidentId}
                    onClick={() => handleIncidentClick(incidentId)}
                    className="px-3 py-1 bg-blue-900/30 hover:bg-blue-900/50 border border-blue-500/30 hover:border-blue-500/50 rounded text-sm text-blue-400 hover:text-blue-300 transition-colors font-mono"
                  >
                    {incidentId}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-slate-800/30 border-t border-slate-700 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            {isPlaying ? 'Playing audio response...' : 'Response ready'}
          </div>
          <button
            onClick={handleClose}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
