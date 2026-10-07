/**
 * Modal for revealing PII with reason requirement
 */

import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ptBR } from '../../lib/i18n/ptBR';
import { useEditorStore } from '../../store/editorSlice';
import { generateMockPIIValue } from '../../lib/hitl/mock';

interface RevealPiiModalProps {
  entityId: string;
  entityType: string;
  entityToken: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const RevealPiiModal: React.FC<RevealPiiModalProps> = ({
  entityId,
  entityType,
  entityToken,
  open,
  onOpenChange,
}) => {
  const [reason, setReason] = useState('');
  const [isRevealing, setIsRevealing] = useState(false);
  const { revealPII, revealedPII } = useEditorStore();

  const revealed = revealedPII.get(entityId);

  const handleConfirm = () => {
    if (!reason.trim()) {
      return;
    }

    setIsRevealing(true);
    
    // Generate mock PII value (in production, this would call PII vault API)
    const value = generateMockPIIValue(entityType, entityToken);
    
    revealPII(entityId, value, reason);
    
    setIsRevealing(false);
    setReason('');
  };

  const handleClose = () => {
    setReason('');
    onOpenChange(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={handleClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-lg p-6 w-full max-w-md z-50">
          <Dialog.Title className="text-lg font-semibold text-gray-900 mb-4">
            {ptBR.revealPII.title}
          </Dialog.Title>

          {revealed ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm font-medium text-green-800 mb-2">
                  {ptBR.revealPII.revealed}
                </p>
                <p className="text-sm text-green-700 font-mono">{revealed.value}</p>
                <p className="text-xs text-green-600 mt-2">
                  Motivo: {revealed.reason}
                </p>
              </div>
              <div className="flex justify-end">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                >
                  {ptBR.common.close}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {ptBR.revealPII.reasonLabel}
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder={ptBR.revealPII.reasonPlaceholder}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={4}
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                >
                  {ptBR.common.cancel}
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={!reason.trim() || isRevealing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isRevealing ? ptBR.common.loading : ptBR.common.confirm}
                </button>
              </div>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};


