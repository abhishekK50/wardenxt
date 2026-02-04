'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Play, CheckCircle, AlertTriangle, Shield, Clock, FileDown } from 'lucide-react';
import { Runbook, RunbookStep, RunbookCommand } from '@/lib/api';

interface RunbookPanelProps {
  runbook: Runbook;
  onExecuteCommand: (stepNumber: number, commandIndex: number, command: RunbookCommand) => void;
  onExport: () => void;
  executedSteps?: Set<number>;
}

export default function RunbookPanel({
  runbook,
  onExecuteCommand,
  onExport,
  executedSteps = new Set()
}: RunbookPanelProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([1]));
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null);

  const toggleStep = (stepNumber: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepNumber)) {
      newExpanded.delete(stepNumber);
    } else {
      newExpanded.add(stepNumber);
    }
    setExpandedSteps(newExpanded);
  };

  const expandAll = () => {
    setExpandedSteps(new Set(runbook.steps.map(s => s.step_number)));
  };

  const collapseAll = () => {
    setExpandedSteps(new Set());
  };

  const copyCommand = async (command: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopiedCommand(command);
      setTimeout(() => setCopiedCommand(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'diagnostic':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'remediation':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'verification':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'rollback':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'safe':
        return 'text-green-400';
      case 'medium':
        return 'text-yellow-400';
      case 'high':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  const completedSteps = executedSteps.size;
  const progressPercent = (completedSteps / runbook.total_steps) * 100;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 border-b border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">
              🛠️ Automated Runbook
            </h2>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-400">
                {runbook.total_steps} steps
              </span>
              <span className="text-slate-600">•</span>
              <div className="flex items-center gap-1 text-slate-400">
                <Clock className="h-4 w-4" />
                {runbook.estimated_total_time}
              </div>
              <span className="text-slate-600">•</span>
              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                runbook.severity === 'P0' ? 'bg-red-500/20 text-red-400' :
                runbook.severity === 'P1' ? 'bg-orange-500/20 text-orange-400' :
                'bg-yellow-500/20 text-yellow-400'
              }`}>
                {runbook.severity}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={expandAll}
              className="px-3 py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Collapse All
            </button>
            <button
              onClick={onExport}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 text-sm font-semibold transition-all"
            >
              <FileDown className="h-4 w-4" />
              Export
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2 text-sm">
            <span className="text-slate-400">Progress</span>
            <span className="text-white font-semibold">
              {completedSteps} / {runbook.total_steps} steps completed
            </span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Warnings */}
        {runbook.warnings.length > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-yellow-400 mb-2">Important Warnings</h3>
                <ul className="space-y-1">
                  {runbook.warnings.map((warning, i) => (
                    <li key={i} className="text-sm text-yellow-300">• {warning}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Prerequisites */}
        {runbook.prerequisites.length > 0 && (
          <div className="mt-3 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <Shield className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-blue-400 mb-2">Prerequisites</h3>
                <ul className="space-y-1">
                  {runbook.prerequisites.map((prereq, i) => (
                    <li key={i} className="text-sm text-blue-300">• {prereq}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Steps */}
      <div className="divide-y divide-slate-800">
        {runbook.steps.map((step) => {
          const isExpanded = expandedSteps.has(step.step_number);
          const isCompleted = executedSteps.has(step.step_number);

          return (
            <div key={step.step_number} className="bg-slate-900/30">
              {/* Step Header */}
              <button
                onClick={() => toggleStep(step.step_number)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      isCompleted
                        ? 'bg-green-500 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {isCompleted ? <CheckCircle className="h-5 w-5" /> : step.step_number}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCategoryColor(step.category)}`}>
                      {step.category}
                    </span>
                  </div>

                  <div className="text-left">
                    <h3 className="text-lg font-semibold text-white">{step.title}</h3>
                    <p className="text-sm text-slate-400">{step.commands.length} command{step.commands.length !== 1 ? 's' : ''} • {step.estimated_duration}</p>
                  </div>
                </div>

                {isExpanded ? (
                  <ChevronUp className="h-5 w-5 text-slate-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-slate-400" />
                )}
              </button>

              {/* Step Content */}
              {isExpanded && (
                <div className="px-6 pb-6 space-y-4">
                  {step.commands.map((command, cmdIndex) => (
                    <div
                      key={cmdIndex}
                      className="bg-slate-950/50 border border-slate-700 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-sm font-semibold ${getRiskColor(command.risk_level)}`}>
                              Risk: {command.risk_level.toUpperCase()}
                            </span>
                            {command.requires_approval && (
                              <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">
                                Approval Required
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-300 mb-3">{command.description}</p>
                        </div>
                      </div>

                      {/* Command */}
                      <div className="relative">
                        <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-sm text-green-400 font-mono overflow-x-auto">
                          {command.command}
                        </pre>
                        <div className="absolute top-2 right-2 flex gap-2">
                          <button
                            onClick={() => copyCommand(command.command)}
                            className="p-2 bg-slate-800 hover:bg-slate-700 rounded transition-colors"
                            title="Copy command"
                          >
                            <Copy className={`h-4 w-4 ${
                              copiedCommand === command.command ? 'text-green-400' : 'text-slate-400'
                            }`} />
                          </button>
                          <button
                            onClick={() => onExecuteCommand(step.step_number, cmdIndex, command)}
                            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-1 text-sm font-semibold transition-all"
                          >
                            <Play className="h-3 w-3" />
                            Execute
                          </button>
                        </div>
                      </div>

                      {/* Expected Output */}
                      {command.expected_output && (
                        <div className="mt-3">
                          <p className="text-xs text-slate-500 mb-1">Expected Output:</p>
                          <pre className="bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-400 font-mono">
                            {command.expected_output}
                          </pre>
                        </div>
                      )}

                      {/* Timeout */}
                      <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                        <span>Timeout: {command.timeout_seconds}s</span>
                      </div>
                    </div>
                  ))}

                  {/* Prerequisites Warning */}
                  {step.prerequisite_steps.length > 0 && (
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded p-3 text-sm">
                      <span className="text-orange-400 font-semibold">⚠️ Prerequisites:</span>
                      <span className="text-orange-300 ml-2">
                        Complete step{step.prerequisite_steps.length > 1 ? 's' : ''} {step.prerequisite_steps.join(', ')} first
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
