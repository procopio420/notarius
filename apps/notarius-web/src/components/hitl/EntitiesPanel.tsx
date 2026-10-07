/**
 * Left sidebar panel for Entities & Tokens
 */

import React, { useState, useMemo } from 'react';
import { Editor } from '@tiptap/react';
import { ptBR } from '../../lib/i18n/ptBR';
import { useEditorStore } from '../../store/editorSlice';
import { getSelectionRange, addEntityLink } from '../../lib/hitl/tiptap';
import { RevealPiiModal } from './RevealPiiModal';
import { AuditLog } from './AuditLog';

interface EntitiesPanelProps {
  editor: Editor | null;
}

export const EntitiesPanel: React.FC<EntitiesPanelProps> = ({ editor }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [revealModalEntity, setRevealModalEntity] = useState<{
    id: string;
    type: string;
    token: string;
  } | null>(null);

  const { getEntities, addEntityLink: addLink, revealedPII } = useEditorStore();
  const entities = getEntities();

  const filteredEntities = useMemo(() => {
    if (!searchQuery.trim()) {
      return entities;
    }
    const query = searchQuery.toLowerCase();
    return entities.filter(
      (entity) =>
        entity.label.toLowerCase().includes(query) ||
        entity.token.toLowerCase().includes(query) ||
        entity.type.toLowerCase().includes(query)
    );
  }, [entities, searchQuery]);

  const handleRevealPII = (entity: { id: string; type: string; token: string }) => {
    setRevealModalEntity(entity);
  };

  const handleLinkToSelection = (entityId: string) => {
    if (!editor) {
      return;
    }

    const range = getSelectionRange(editor);
    if (!range) {
      alert(ptBR.entitiesPanel.noSelection);
      return;
    }

    addEntityLink(editor, range, entityId);
    addLink(entityId, range.from, range.to);
  };

  const getEntityIcon = (type: string) => {
    const icons: Record<string, string> = {
      name: '👤',
      cpf: '🆔',
      cnpj: '🏢',
      address: '📍',
      phone: '📞',
      email: '📧',
    };
    return icons[type.toLowerCase()] || '❓';
  };

  return (
    <div className="w-80 border-r border-gray-200 bg-gray-50 flex flex-col overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          {ptBR.entitiesPanel.title}
        </h3>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={ptBR.entitiesPanel.searchPlaceholder}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        />
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {filteredEntities.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            {ptBR.entitiesPanel.noEntities}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEntities.map((entity) => {
              const revealed = revealedPII.get(entity.id);
              return (
                <div
                  key={entity.id}
                  className="p-3 bg-white border border-gray-200 rounded-lg"
                >
                  <div className="flex items-start gap-2 mb-2">
                    <span className="text-lg">{getEntityIcon(entity.type)}</span>
                    <div className="flex-1">
                      <h4 className="font-medium text-sm text-gray-900">
                        {entity.label}
                      </h4>
                      <p className="text-xs text-gray-600 mt-1">
                        {entity.token}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {entity.scope}
                      </p>
                    </div>
                  </div>

                  {revealed && (
                    <div className="mb-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
                      <p className="text-green-800 font-medium">
                        {ptBR.revealPII.revealed}
                      </p>
                      <p className="text-green-700 font-mono">{revealed.value}</p>
                    </div>
                  )}

                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => handleRevealPII(entity)}
                      className="flex-1 px-2 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                    >
                      {ptBR.entitiesPanel.revealPII}
                    </button>
                    <button
                      onClick={() => handleLinkToSelection(entity.id)}
                      className="flex-1 px-2 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
                    >
                      {ptBR.entitiesPanel.linkToSelection}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-200">
        <AuditLog />
      </div>

      {revealModalEntity && (
        <RevealPiiModal
          entityId={revealModalEntity.id}
          entityType={revealModalEntity.type}
          entityToken={revealModalEntity.token}
          open={!!revealModalEntity}
          onOpenChange={(open) => !open && setRevealModalEntity(null)}
        />
      )}
    </div>
  );
};


