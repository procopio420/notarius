/**
 * Placeholder Highlight Component for displaying PII placeholders
 */

import React, { useState } from 'react';
import { Placeholder } from '../../types/editor';
import axios from 'axios';

interface PlaceholderHighlightProps {
  placeholder: Placeholder;
  onResolve?: (placeholder: Placeholder) => void;
  showResolveButton?: boolean;
}

export const PlaceholderHighlight: React.FC<PlaceholderHighlightProps> = ({
  placeholder,
  onResolve,
  showResolveButton = false,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [resolvedValue, setResolvedValue] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResolve = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsResolving(true);
    setError(null);

    try {
      const token = localStorage.getItem('auth_token');
      const tenantId = localStorage.getItem('tenant_id');

      const response = await axios.post(
        'http://localhost:8002/api/v1/retrieve-pii',
        {
          token: placeholder.token,
          tenant_id: tenantId,
        },
        {
          headers: {
            Authorization: `Token ${token}`,
          },
        }
      );

      setResolvedValue(response.data.pii_value);
      if (onResolve) {
        onResolve(placeholder);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Não autorizado');
      console.error('Failed to resolve placeholder:', err);
    } finally {
      setIsResolving(false);
    }
  };
  const getPlaceholderColor = (type: Placeholder['type']) => {
    switch (type) {
      case 'name':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'cpf':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'cnpj':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'address':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'phone':
        return 'bg-pink-100 text-pink-800 border-pink-200';
      case 'email':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPlaceholderIcon = (type: Placeholder['type']) => {
    switch (type) {
      case 'name':
        return '👤';
      case 'cpf':
        return '🆔';
      case 'cnpj':
        return '🏢';
      case 'address':
        return '📍';
      case 'phone':
        return '📞';
      case 'email':
        return '📧';
      default:
        return '❓';
    }
  };

  return (
    <span
      className="relative inline-block"
      data-placeholder-type={placeholder.type.toUpperCase()}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span
        className={`
          inline-flex items-center gap-1 px-2 py-1 rounded-md border text-sm font-medium
          placeholder-highlight
          ${getPlaceholderColor(placeholder.type)}
          hover:shadow-sm transition-shadow cursor-pointer
        `}
        title={`${placeholder.type.toUpperCase()}: ${placeholder.token}`}
      >
        <span>{getPlaceholderIcon(placeholder.type)}</span>
        <span>{resolvedValue || placeholder.displayText}</span>
        {showResolveButton && !resolvedValue && (
          <button
            onClick={handleResolve}
            disabled={isResolving}
            className="ml-1 text-xs hover:bg-white/50 rounded px-1 disabled:opacity-50"
            title="Resolver placeholder"
            data-testid="resolve-placeholder-button"
          >
            {isResolving ? '⏳' : '🔓'}
          </button>
        )}
      </span>
      
      {/* Tooltip */}
      {showTooltip && (
        <div
          className="absolute z-50 bottom-full left-0 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg whitespace-nowrap"
          data-testid="placeholder-tooltip"
        >
          <div className="font-bold">{placeholder.type.toUpperCase()}</div>
          <div className="text-gray-300">{placeholder.token}</div>
          {resolvedValue && (
            <div className="mt-1 text-green-300 font-medium" data-testid="resolved-value">
              ✓ {resolvedValue}
            </div>
          )}
          {error && (
            <div className="mt-1 text-red-300 text-xs">
              ⚠ {error}
            </div>
          )}
          <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </span>
  );
};

export default PlaceholderHighlight;
