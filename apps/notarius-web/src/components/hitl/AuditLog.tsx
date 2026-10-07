/**
 * Audit log component showing last 10 events
 */

import React from 'react';
import { ptBR } from '../../lib/i18n/ptBR';
import { useEditorStore } from '../../store/editorSlice';

export const AuditLog: React.FC = () => {
  const { auditEvents } = useEditorStore();
  const recentEvents = auditEvents.slice(0, 10);

  const formatTimestamp = (timestamp: Date): string => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);

    if (minutes < 1) {
      return ptBR.audit.justNow;
    } else if (minutes < 60) {
      return `${minutes} ${ptBR.audit.minutesAgo}`;
    } else if (hours < 24) {
      return `${hours} ${ptBR.audit.hoursAgo}`;
    } else {
      return timestamp.toLocaleString('pt-BR');
    }
  };

  const getActionLabel = (action: string): string => {
    return ptBR.audit.actions[action as keyof typeof ptBR.audit.actions] || action;
  };

  if (recentEvents.length === 0) {
    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">
          {ptBR.entitiesPanel.auditLog.title}
        </h4>
        <p className="text-xs text-gray-500">
          {ptBR.entitiesPanel.auditLog.noEvents}
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        {ptBR.entitiesPanel.auditLog.title}
      </h4>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {recentEvents.map((event) => (
          <div
            key={event.id}
            className="p-2 bg-white border border-gray-200 rounded text-xs"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-gray-900">
                {getActionLabel(event.action)}
              </span>
              <span className="text-gray-500">
                {formatTimestamp(event.timestamp)}
              </span>
            </div>
            {event.reason && (
              <p className="text-gray-600 mt-1 line-clamp-2">
                {event.reason}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};


