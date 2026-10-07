/**
 * Checklist panel - Run checks and display issues
 */

import React, { useState } from 'react';
import { ptBR } from '../../lib/i18n/ptBR';
import { useEditorStore } from '../../store/editorSlice';

export const ChecklistPanel: React.FC = () => {
  const { issues, runChecks } = useEditorStore();
  const [isRunning, setIsRunning] = useState(false);

  const handleRunChecks = () => {
    setIsRunning(true);
    runChecks();
    setTimeout(() => setIsRunning(false), 500);
  };

  const blockers = issues.filter((i) => i.severity === 'Bloqueador');
  const alerts = issues.filter((i) => i.severity === 'Alerta');
  const informative = issues.filter((i) => i.severity === 'Informativo');

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      Bloqueador: 'bg-red-100 text-red-800 border-red-200',
      Alerta: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      Informativo: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {ptBR.checklist.title}
          </h3>
          <button
            onClick={handleRunChecks}
            disabled={isRunning}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {isRunning ? ptBR.checklist.running : ptBR.checklist.runChecks}
          </button>
        </div>

        {issues.length > 0 && (
          <div className="flex gap-3">
            <div className="flex-1 p-2 bg-red-50 border border-red-200 rounded text-center">
              <p className="text-xs text-red-600 font-medium">
                {ptBR.checklist.counts.blockers}
              </p>
              <p className="text-lg font-bold text-red-800">{blockers.length}</p>
            </div>
            <div className="flex-1 p-2 bg-yellow-50 border border-yellow-200 rounded text-center">
              <p className="text-xs text-yellow-600 font-medium">
                {ptBR.checklist.counts.alerts}
              </p>
              <p className="text-lg font-bold text-yellow-800">{alerts.length}</p>
            </div>
            <div className="flex-1 p-2 bg-blue-50 border border-blue-200 rounded text-center">
              <p className="text-xs text-blue-600 font-medium">
                {ptBR.checklist.counts.informative}
              </p>
              <p className="text-lg font-bold text-blue-800">{informative.length}</p>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {issues.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            {ptBR.checklist.noIssues}
          </div>
        ) : (
          <div className="space-y-3">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className={`p-3 border rounded-lg ${getSeverityColor(issue.severity)}`}
              >
                <div className="flex items-start justify-between mb-1">
                  <span className="text-xs font-medium">
                    {issue.severity}
                  </span>
                  {issue.rule && (
                    <span className="text-xs opacity-75">{issue.rule}</span>
                  )}
                </div>
                <p className="text-sm mt-1">{issue.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

