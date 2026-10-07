/**
 * Grounding panel (Fundamentação tab) - Citations with attachment
 */

import React, { useMemo } from 'react';
import { Editor } from '@tiptap/react';
import { ptBR } from '../../lib/i18n/ptBR';
import { useEditorStore } from '../../store/editorSlice';
import { getSelectionRange, addGrounding } from '../../lib/hitl/tiptap';
import { CitationTooltip } from '../citations/CitationTooltip';

interface GroundingPanelProps {
  editor: Editor | null;
}

export const GroundingPanel: React.FC<GroundingPanelProps> = ({ editor }) => {
  const { minuta, groundingLinks, addGroundingLink } = useEditorStore();

  const handleAttachCitation = (citationId: string) => {
    if (!editor) {
      return;
    }

    const range = getSelectionRange(editor);
    if (!range) {
      alert(ptBR.grounding.noSelection);
      return;
    }

    addGrounding(editor, range, citationId);
    addGroundingLink(citationId, range.from, range.to);
  };

  // Calculate coverage percentage
  const coverage = useMemo(() => {
    if (!editor) {
      return 0;
    }

    const totalLength = editor.state.doc.content.size;
    if (totalLength === 0) {
      return 0;
    }

    let coveredLength = 0;
    groundingLinks.forEach((link) => {
      coveredLength += Math.max(0, link.to - link.from);
    });

    return Math.min(100, Math.round((coveredLength / totalLength) * 100));
  }, [editor, groundingLinks]);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {ptBR.grounding.title}
        </h3>
        <div className="mt-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-700">
              {ptBR.grounding.coverage}
            </span>
            <span className="text-sm font-medium text-gray-900">{coverage}%</span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                coverage >= 70
                  ? 'bg-green-500'
                  : coverage >= 40
                  ? 'bg-yellow-500'
                  : 'bg-orange-500'
              }`}
              style={{ width: `${coverage}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {ptBR.grounding.coverageDescription}
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {minuta.citations && minuta.citations.length > 0 ? (
          <div className="space-y-3">
            {minuta.citations.map((citation) => (
              <CitationTooltip key={citation.id} citation={citation}>
                <div className="p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-sm text-gray-900">
                      {citation.title}
                    </h4>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        citation.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {citation.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{citation.anchor}</p>
                  <p className="text-xs text-gray-700 italic line-clamp-2 mb-2">
                    "{citation.snippet}"
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAttachCitation(citation.id);
                    }}
                    className="w-full mt-2 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                  >
                    {ptBR.grounding.attachToSelection}
                  </button>
                </div>
              </CitationTooltip>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 text-sm">
            {ptBR.grounding.noCitations}
          </div>
        )}
      </div>
    </div>
  );
};


