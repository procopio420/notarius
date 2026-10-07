/**
 * Citation List Component for displaying all citations in a minuta
 */

import React from 'react';
import { Citation } from '../../types/editor';
import { CitationTooltip } from './CitationTooltip';

interface CitationListProps {
  citations: Citation[];
  onCitationClick?: (citation: Citation) => void;
  showConfidence?: boolean;
  showStatus?: boolean;
}

export const CitationList: React.FC<CitationListProps> = ({
  citations,
  onCitationClick,
  showConfidence = true,
  showStatus = true,
}) => {
  if (citations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Nenhuma citação encontrada neste documento.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="citations-panel">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          Citações Legais ({citations.length})
        </h3>
        <div className="text-sm text-gray-500" data-testid="grounding-confidence">
          Confiança média: {Math.round(
            citations.reduce((acc, c) => acc + c.confidence, 0) / citations.length * 100
          )}%
        </div>
      </div>

      <div className="space-y-3">
        {citations.map((citation, index) => (
          <div
            key={citation.id}
            className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
            onClick={() => onCitationClick?.(citation)}
            data-testid="citation-item"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 
                    className="font-medium text-gray-900"
                    data-testid="citation-source"
                  >
                    {citation.title}
                  </h4>
                  {showStatus && (
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      citation.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : citation.status === 'revoked'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {citation.status}
                    </span>
                  )}
                </div>
                
                <p 
                  className="text-sm text-gray-600 mb-2"
                  data-testid="citation-article"
                >
                  <strong>{citation.anchor}</strong> - Vigente desde {new Date(citation.effective_date).toLocaleDateString('pt-BR')}
                </p>
                
                <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded italic" data-testid="citation-excerpt">
                  "{citation.snippet}"
                </p>
              </div>
              
              <div className="flex flex-col items-end gap-2 ml-4">
                {showConfidence && (
                  <div className="flex items-center gap-1">
                    <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          citation.confidence >= 0.8 ? 'bg-green-500' :
                          citation.confidence >= 0.6 ? 'bg-yellow-500' :
                          'bg-orange-500'
                        }`}
                        style={{ width: `${citation.confidence * 100}%` }}
                        data-testid="confidence-indicator"
                      />
                    </div>
                    <span 
                      className="text-xs text-gray-500"
                      data-testid="citation-confidence"
                    >
                      {Math.round(citation.confidence * 100)}%
                    </span>
                  </div>
                )}
                
                <a
                  href={citation.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                  onClick={(e) => e.stopPropagation()}
                  data-testid="citation-link"
                >
                  Ver fonte
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CitationList;
