/**
 * Modal for approval override when blockers exist
 */

import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ptBR } from '../../lib/i18n/ptBR';

interface OverrideApproveModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (justification: string) => void;
  blockerCount: number;
}

export const OverrideApproveModal: React.FC<OverrideApproveModalProps> = ({
  open,
  onOpenChange,
  onConfirm,
  blockerCount,
}) => {
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');

  const handleConfirm = () => {
    if (!justification.trim()) {
      setError(ptBR.approvalOverride.required);
      return;
    }

    onConfirm(justification);
    setJustification('');
    setError('');
    onOpenChange(false);
  };

  const handleClose = () => {
    setJustification('');
    setError('');
    onOpenChange(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={handleClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-lg p-6 w-full max-w-md z-50">
          <Dialog.Title className="text-lg font-semibold text-gray-900 mb-4">
            {ptBR.approvalOverride.title}
          </Dialog.Title>

          <div className="space-y-4">
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                {ptBR.approvalOverride.message}
              </p>
              <p className="text-xs text-yellow-700 mt-2">
                Problemas bloqueadores encontrados: {blockerCount}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {ptBR.approvalOverride.justificationLabel}
              </label>
              <textarea
                value={justification}
                onChange={(e) => {
                  setJustification(e.target.value);
                  setError('');
                }}
                placeholder={ptBR.approvalOverride.justificationPlaceholder}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={4}
              />
              {error && (
                <p className="mt-1 text-sm text-red-600">{error}</p>
              )}
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
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                {ptBR.approvalOverride.confirm}
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};


