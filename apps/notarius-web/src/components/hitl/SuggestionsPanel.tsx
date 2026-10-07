/**
 * Suggestions panel - AI suggestions with apply/reject/edit
 */

import React, { useState } from 'react';
import { Editor } from '@tiptap/react';
import { ptBR } from '../../lib/i18n/ptBR';
import { useEditorStore } from '../../store/editorSlice';
import { Suggestion } from '../../types/editor';
import * as Dialog from '@radix-ui/react-dialog';

interface SuggestionsPanelProps {
  editor: Editor | null;
}

export const SuggestionsPanel: React.FC<SuggestionsPanelProps> = ({ editor }) => {
  const { suggestions, applySuggestion, rejectSuggestion } = useEditorStore();
  const [editingSuggestion, setEditingSuggestion] = useState<Suggestion | null>(null);
  const [editedText, setEditedText] = useState('');

  const handleApply = (suggestionId: string) => {
    applySuggestion(suggestionId, editor);
  };

  const handleReject = (suggestionId: string) => {
    rejectSuggestion(suggestionId);
  };

  const handleEdit = (suggestion: Suggestion) => {
    setEditingSuggestion(suggestion);
    setEditedText(suggestion.afterText);
  };

  const handleSaveEdit = () => {
    if (!editingSuggestion) {
      return;
    }

    // Create a modified suggestion
    const modified: Suggestion = {
      ...editingSuggestion,
      afterText: editedText,
    };

    // Apply the modified suggestion
    if (editor) {
      const { from, to } = modified.targetRange;
      if (modified.kind === 'INSERT') {
        editor.chain().focus().insertContentAt(from, editedText).run();
      } else if (modified.kind === 'REPLACE') {
        editor.chain().focus().setTextSelection({ from, to }).insertContent(editedText).run();
      } else if (modified.kind === 'REMOVE') {
        editor.chain().focus().setTextSelection({ from, to }).deleteSelection().run();
      }
    }

    // Remove from suggestions
    rejectSuggestion(editingSuggestion.id);
    setEditingSuggestion(null);
    setEditedText('');
  };

  const getKindLabel = (kind: string) => {
    const labels: Record<string, string> = {
      INSERT: ptBR.suggestions.kind.insert,
      REPLACE: ptBR.suggestions.kind.replace,
      REMOVE: ptBR.suggestions.kind.remove,
    };
    return labels[kind] || kind;
  };

  const getKindColor = (kind: string) => {
    const colors: Record<string, string> = {
      INSERT: 'bg-green-100 text-green-800',
      REPLACE: 'bg-blue-100 text-blue-800',
      REMOVE: 'bg-red-100 text-red-800',
    };
    return colors[kind] || 'bg-gray-100 text-gray-800';
  };

  if (suggestions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <p className="text-gray-500 text-sm">{ptBR.suggestions.noSuggestions}</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="space-y-4">
        {suggestions.map((suggestion) => (
          <div
            key={suggestion.id}
            className="p-4 bg-white border border-gray-200 rounded-lg"
          >
            <div className="flex items-center justify-between mb-3">
              <span
                className={`px-2 py-1 text-xs font-medium rounded ${getKindColor(
                  suggestion.kind
                )}`}
              >
                {getKindLabel(suggestion.kind)}
              </span>
              <span className="text-xs text-gray-600">
                {ptBR.suggestions.confidence}: {Math.round(suggestion.confidence * 100)}%
              </span>
            </div>

            {suggestion.kind !== 'INSERT' && suggestion.beforeText && (
              <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                <p className="text-red-800 font-medium mb-1">Antes:</p>
                <p className="text-red-700 line-through">{suggestion.beforeText}</p>
              </div>
            )}

            <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-xs">
              <p className="text-green-800 font-medium mb-1">Depois:</p>
              <p className="text-green-700">{suggestion.afterText || '(remover)'}</p>
            </div>

            {suggestion.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {suggestion.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                  >
                    {ptBR.suggestions.tags[tag.toLowerCase() as keyof typeof ptBR.suggestions.tags] || tag}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => handleApply(suggestion.id)}
                className="flex-1 px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
              >
                {ptBR.suggestions.apply}
              </button>
              <button
                onClick={() => handleReject(suggestion.id)}
                className="flex-1 px-3 py-1.5 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 transition-colors"
              >
                {ptBR.suggestions.reject}
              </button>
              <button
                onClick={() => handleEdit(suggestion)}
                className="flex-1 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
              >
                {ptBR.suggestions.edit}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Dialog */}
      {editingSuggestion && (
        <Dialog.Root open={!!editingSuggestion} onOpenChange={(open) => !open && setEditingSuggestion(null)}>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
            <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-lg p-6 w-full max-w-md z-50">
              <Dialog.Title className="text-lg font-semibold text-gray-900 mb-4">
                {ptBR.suggestions.editDialog.title}
              </Dialog.Title>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {ptBR.suggestions.editDialog.afterTextLabel}
                  </label>
                  <textarea
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows={6}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setEditingSuggestion(null)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    {ptBR.common.cancel}
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {ptBR.suggestions.editDialog.save}
                  </button>
                </div>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      )}
    </div>
  );
};


