'use client';

import { useState } from 'react';
import { X, AlertTriangle, Play, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { RunbookCommand, ExecutionResult } from '@/lib/api';

interface CommandExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  command: RunbookCommand | null;
  stepNumber: number;
  commandIndex: number;
  onExecute: (dryRun: boolean, confirmationText?: string) => Promise<ExecutionResult>;
}

export default function CommandExecutionModal({
  isOpen,
  onClose,
  command,
  stepNumber,
  commandIndex,
  onExecute
}: CommandExecutionModalProps) {
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [confirmationText, setConfirmationText] = useState('');
  const [isDryRun, setIsDryRun] = useState(true);

  if (!isOpen || !command) return null;

  const isHighRisk = command.risk_level === 'high';
  const needsConfirmation = isHighRisk && !isDryRun;
  const confirmationValid = !needsConfirmation || confirmationText === 'EXECUTE';

  const handleExecute = async (dryRun: boolean) => {
    setIsExecuting(true);
    setExecutionResult(null);
    setIsDryRun(dryRun);

    try {
      const result = await onExecute(dryRun, needsConfirmation ? confirmationText : undefined);
      setExecutionResult(result);
    } catch (error) {
      console.error('Execution failed:', error);
      setExecutionResult({
        step_number: stepNumber,
        command_index: commandIndex,
        command: command.command,
        success: false,
        output: '',
        error: error instanceof Error ? error.message : 'Unknown error',
        executed_at: new Date().toISOString(),
        executed_by: 'user',
        dry_run: dryRun,
        duration_seconds: 0
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClose = () => {
    setConfirmationText('');
    setExecutionResult(null);
    setIsDryRun(true);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div>
            <h2 className="text-2xl font-bold text-white">Execute Command</h2>
            <p className="text-sm text-slate-400 mt-1">Step {stepNumber} • Command {commandIndex + 1}</p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Risk Warning */}
          {isHighRisk && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-red-400 font-semibold mb-1">High-Risk Command</h3>
                  <p className="text-sm text-red-300">
                    This command can make significant changes to your system.
                    Review carefully before executing.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Command Info */}
          <div>
            <h3 className="text-sm font-semibold text-slate-400 mb-2">Description</h3>
            <p className="text-white">{command.description}</p>
          </div>

          {/* Command */}
          <div>
            <h3 className="text-sm font-semibold text-slate-400 mb-2">Command</h3>
            <pre className="bg-slate-950 border border-slate-700 rounded-lg p-4 text-sm text-green-400 font-mono overflow-x-auto">
              {command.command}
            </pre>
          </div>

          {/* Expected Output */}
          {command.expected_output && (
            <div>
              <h3 className="text-sm font-semibold text-slate-400 mb-2">Expected Output</h3>
              <pre className="bg-slate-950 border border-slate-700 rounded-lg p-4 text-sm text-slate-300 font-mono overflow-x-auto">
                {command.expected_output}
              </pre>
            </div>
          )}

          {/* High-Risk Confirmation */}
          {isHighRisk && !isDryRun && !executionResult && (
            <div>
              <h3 className="text-sm font-semibold text-red-400 mb-2">Confirmation Required</h3>
              <p className="text-sm text-slate-400 mb-3">
                Type <span className="font-mono text-white bg-slate-800 px-2 py-1 rounded">EXECUTE</span> to confirm:
              </p>
              <input
                type="text"
                value={confirmationText}
                onChange={(e) => setConfirmationText(e.target.value)}
                placeholder="Type EXECUTE to confirm"
                className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                disabled={isExecuting}
              />
            </div>
          )}

          {/* Execution Result */}
          {executionResult && (
            <div className={`rounded-lg p-4 border ${
              executionResult.success
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-start gap-3 mb-3">
                {executionResult.success ? (
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <h3 className={`font-semibold mb-1 ${
                    executionResult.success ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {executionResult.success ? 'Execution Successful' : 'Execution Failed'}
                  </h3>
                  <p className="text-sm text-slate-400">
                    {executionResult.dry_run && (
                      <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded text-xs mr-2">
                        DRY RUN
                      </span>
                    )}
                    Completed in {executionResult.duration_seconds.toFixed(2)}s
                  </p>
                </div>
              </div>

              {/* Output */}
              {executionResult.output && (
                <div>
                  <h4 className="text-xs text-slate-500 mb-2">Output:</h4>
                  <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-xs text-slate-300 font-mono overflow-x-auto max-h-64 overflow-y-auto">
                    {executionResult.output}
                  </pre>
                </div>
              )}

              {/* Error */}
              {executionResult.error && (
                <div className="mt-3">
                  <h4 className="text-xs text-red-400 mb-2">Error:</h4>
                  <pre className="bg-slate-950 border border-red-800 rounded p-3 text-xs text-red-300 font-mono overflow-x-auto">
                    {executionResult.error}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-slate-700">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span>Timeout: {command.timeout_seconds}s</span>
            <span>•</span>
            <span className={`font-semibold ${
              command.risk_level === 'safe' ? 'text-green-400' :
              command.risk_level === 'medium' ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              Risk: {command.risk_level.toUpperCase()}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {!executionResult && (
              <>
                <button
                  onClick={() => handleExecute(true)}
                  disabled={isExecuting}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isExecuting && isDryRun ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Dry Run
                    </>
                  )}
                </button>

                <button
                  onClick={() => handleExecute(false)}
                  disabled={isExecuting || !confirmationValid}
                  className={`px-6 py-3 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 ${
                    isHighRisk
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {isExecuting && !isDryRun ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Execute for Real
                    </>
                  )}
                </button>
              </>
            )}

            <button
              onClick={handleClose}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold transition-all"
            >
              {executionResult ? 'Done' : 'Cancel'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
