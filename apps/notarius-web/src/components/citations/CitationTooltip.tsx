/**
 * Citation Tooltip Component for displaying legal citations
 */

import React from 'react';
import { Citation, CitationTooltipProps } from '../../types/editor';

export const CitationTooltip: React.FC<CitationTooltipProps> = ({ citation, children }) => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="relative inline-block">
      <span
        className="text-blue-600 underline cursor-help hover:text-blue-800 transition-colors"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        data-citation-ref={citation.id}
      >
        {children}
      </span>
      
      {isOpen && (
        <div 
          className="absolute z-50 w-80 p-4 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg"
          data-testid="citation-tooltip"
        >
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 
                className="font-semibold text-gray-900"
                data-testid="citation-source"
              >
                {citation.title}
              </h4>
              <span className={`px-2 py-1 text-xs rounded-full ${
                citation.status === 'active' 
                  ? 'bg-green-100 text-green-800' 
                  : citation.status === 'revoked'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {citation.status}
              </span>
            </div>
            
            <div className="text-sm text-gray-600">
              <p data-testid="citation-article">
                <strong>Artigo:</strong> {citation.anchor}
              </p>
              <p>
                <strong>Data de vigência:</strong> {new Date(citation.effective_date).toLocaleDateString('pt-BR')}
              </p>
            </div>
            
            <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
              <p className="font-medium mb-1">Trecho relevante:</p>
              <p className="italic" data-testid="citation-excerpt">"{citation.snippet}"</p>
            </div>
            
            <div className="flex items-center justify-between">
              <span 
                className="text-xs text-gray-500"
                data-testid="citation-confidence"
              >
                Confiança: {Math.round(citation.confidence * 100)}%
              </span>
              <a
                href={citation.uri}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:text-blue-800 underline"
                data-testid="citation-link"
              >
                Ver fonte original
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationTooltip;
