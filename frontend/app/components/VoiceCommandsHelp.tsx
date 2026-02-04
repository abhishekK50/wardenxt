'use client';

import { useEffect } from 'react';
import { X, Mic, HelpCircle } from 'lucide-react';

interface VoiceCommandsHelpProps {
  onClose: () => void;
}

const commandCategories = [
  {
    category: 'Incident Queries',
    icon: '🔍',
    commands: [
      {
        phrase: 'What\'s the most critical incident?',
        description: 'Find the highest priority incident (P0)'
      },
      {
        phrase: 'Show me P1 incidents',
        description: 'Filter incidents by severity (P0, P1, P2, P3)'
      },
      {
        phrase: 'What happened today?',
        description: 'Query incidents by time range'
      },
      {
        phrase: 'How many incidents are being investigated?',
        description: 'Get count of active investigations'
      }
    ]
  },
  {
    category: 'Analysis Commands',
    icon: '🤖',
    commands: [
      {
        phrase: 'Analyze incident zero zero zero one',
        description: 'Trigger AI analysis on specific incident'
      },
      {
        phrase: 'Analyze incident INC-2026-0001',
        description: 'Alternative format with full ID'
      }
    ]
  },
  {
    category: 'Summaries',
    icon: '📊',
    commands: [
      {
        phrase: 'Summarize all incidents',
        description: 'Get overview of all incidents'
      },
      {
        phrase: 'What\'s the current status?',
        description: 'Overall system health summary'
      },
      {
        phrase: 'Give me an overview',
        description: 'High-level incident summary'
      }
    ]
  }
];

export default function VoiceCommandsHelp({ onClose }: VoiceCommandsHelpProps) {
  useEffect(() => {
    // Close on ESC key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden mx-4 animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-gradient-to-r from-blue-900/20 to-cyan-900/20">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Mic className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Voice Commands</h2>
              <p className="text-sm text-slate-400">Say these phrases to control WardenXT</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(80vh-140px)]">
          <div className="p-6 space-y-6">
            {/* How to Use */}
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-400 mb-2 flex items-center gap-2">
                <HelpCircle className="h-4 w-4" />
                How to Use
              </h3>
              <ol className="text-sm text-slate-300 space-y-1 list-decimal list-inside">
                <li>Click the microphone button (bottom-right corner)</li>
                <li>Wait for the button to turn red</li>
                <li>Speak clearly for up to 5 seconds</li>
                <li>WardenXT will respond with voice and text</li>
              </ol>
            </div>

            {/* Command Categories */}
            {commandCategories.map((category, idx) => (
              <div key={idx} className="space-y-3">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="text-2xl">{category.icon}</span>
                  {category.category}
                </h3>
                <div className="space-y-2">
                  {category.commands.map((cmd, cmdIdx) => (
                    <div
                      key={cmdIdx}
                      className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 hover:border-slate-600 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-1.5 bg-blue-500/10 rounded mt-0.5">
                          <Mic className="h-4 w-4 text-blue-400" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white mb-1">
                            "{cmd.phrase}"
                          </p>
                          <p className="text-xs text-slate-400">{cmd.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Tips */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">💡 Tips</h3>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                <li>Speak clearly in a quiet environment for best results</li>
                <li>You can say "incident zero zero zero one" or "incident INC-2026-0001"</li>
                <li>Use severity levels: P0 (critical), P1 (high), P2 (medium), P3 (low)</li>
                <li>Audio responses will play automatically</li>
                <li>Click on incident IDs in responses to navigate</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-700 bg-slate-800/30 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Powered by Gemini 2.0 Flash
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}
