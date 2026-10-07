/**
 * HITL Editor Component - Main editor for legal documents
 */

import React, { useEffect, useCallback, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Highlight from '@tiptap/extension-highlight';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import Link from '@tiptap/extension-link';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import CharacterCount from '@tiptap/extension-character-count';
import Typography from '@tiptap/extension-typography';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import Strike from '@tiptap/extension-strike';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import { Table } from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import Gapcursor from '@tiptap/extension-gapcursor';
import Dropcursor from '@tiptap/extension-dropcursor';
import Image from '@tiptap/extension-image';
import { createLowlight, common } from 'lowlight';

import { EditorProps } from '../../types/editor';
import { useEditorStore } from '../../store/editorSlice';
import { EditorToolbar } from './EditorToolbar';
import { PlaceholderHighlight } from './PlaceholderHighlight';
import { CitationTooltip } from '../citations/CitationTooltip';
import { EntityLinkMark } from '../hitl/marks/EntityLinkMark';
import { GroundingMark } from '../hitl/marks/GroundingMark';
import { AiRangeMark } from '../hitl/marks/AiRangeMark';
import { EntitiesPanel } from '../hitl/EntitiesPanel';
import { HITLRightSidebar } from '../hitl/HITLRightSidebar';
import { OverrideApproveModal } from '../hitl/OverrideApproveModal';

export const HITLEditor: React.FC<EditorProps> = ({
  minuta,
  onSave,
  onApprove,
  onReject,
  onExplainClause,
  readOnly = false,
  showCitations = true,
  showPlaceholders = true,
}) => {
  const {
    currentContent,
    citationsVisible,
    placeholdersResolved,
    isEditing,
    editConfidence,
    setMinuta,
    updateContent,
    toggleCitations,
    togglePlaceholders,
    getPlaceholders,
    issues,
    logAuditEvent,
  } = useEditorStore();

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Digite o conteúdo do documento...',
        showOnlyWhenEditable: true,
      }),
      Highlight.configure({
        multicolor: true,
      }),
      TextStyle,
      Color,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 underline cursor-pointer',
        },
      }),
      TaskList,
      TaskItem.configure({
        nested: true,
      }),
      CharacterCount,
      Typography,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Underline,
      Strike,
      CodeBlockLowlight.configure({
        lowlight: createLowlight(common),
      }),
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
      Gapcursor,
      Dropcursor,
      Image,
      // HITL marks
      EntityLinkMark,
      GroundingMark,
      AiRangeMark,
    ],
    content: currentContent,
    editable: !readOnly,
    onUpdate: ({ editor }) => {
      const content = editor.getHTML();
      updateContent(content);
    },
  });

  // Initialize editor with minuta data
  useEffect(() => {
    setMinuta(minuta);
  }, [minuta, setMinuta]);

  // Update editor content when store changes
  useEffect(() => {
    if (editor && currentContent !== editor.getHTML()) {
      editor.commands.setContent(currentContent, false);
    }
  }, [currentContent, editor]);

  const handleSave = useCallback(() => {
    if (editor) {
      const content = editor.getHTML();
      onSave(content);
    }
  }, [editor, onSave]);

  const handleReject = useCallback(() => {
    logAuditEvent({ action: 'REJECTED' });
    onReject();
  }, [onReject, logAuditEvent]);

  const handleToggleCitations = useCallback(() => {
    toggleCitations();
  }, [toggleCitations]);

  const blockers = issues.filter((i) => i.severity === 'Bloqueador');
  const hasBlockers = blockers.length > 0;
  const baseCanApprove = minuta.status === 'pronto' && editConfidence >= 0.7;
  const canApprove = baseCanApprove && !hasBlockers;

  const [showOverrideModal, setShowOverrideModal] = useState(false);

  const handleApprove = useCallback(() => {
    logAuditEvent({ action: 'APPROVED' });
    onApprove();
  }, [onApprove, logAuditEvent]);

  const handleApproveClick = useCallback(() => {
    if (hasBlockers) {
      setShowOverrideModal(true);
    } else {
      handleApprove();
    }
  }, [hasBlockers, handleApprove]);

  const handleApproveWithOverride = useCallback(
    (justification: string) => {
      logAuditEvent({
        action: 'APPROVED_WITH_OVERRIDE',
        reason: justification,
      });
      handleApprove();
      setShowOverrideModal(false);
    },
    [handleApprove, logAuditEvent]
  );

  // Render placeholders in the content
  const renderContentWithPlaceholders = (content: string) => {
    if (!showPlaceholders || placeholdersResolved) {
      return content;
    }

    const placeholders = getPlaceholders();
    let renderedContent = content;

    // Replace placeholders with highlighted components
    placeholders.forEach((placeholder) => {
      const placeholderRegex = new RegExp(placeholder.token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
      renderedContent = renderedContent.replace(
        placeholderRegex,
        `<span class="placeholder-highlight" data-placeholder-id="${placeholder.id}">${placeholder.displayText}</span>`
      );
    });

    return renderedContent;
  };

  if (!editor) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Carregando editor...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Metadata Bar */}
      <div className="border-b border-gray-200 px-4 py-2 bg-gray-50 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <span data-testid="minuta-version">
            Versão {minuta.versao}
          </span>
          <span 
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              minuta.status === 'aprovado' ? 'bg-green-100 text-green-800' :
              minuta.status === 'rascunho' ? 'bg-yellow-100 text-yellow-800' :
              minuta.status === 'rejeitado' ? 'bg-red-100 text-red-800' :
              minuta.status === 'finalizado' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}
            data-testid="minuta-status"
          >
            {minuta.status}
          </span>
          <span className="text-gray-600" data-testid="minuta-created-by">
            Criado por: {minuta.created_by}
          </span>
          {minuta.approved_by && (
            <span className="text-gray-600" data-testid="approved-by">
              Aprovado por: {minuta.approved_by}
            </span>
          )}
          {minuta.approved_at && (
            <span className="text-gray-600" data-testid="approved-at">
              em {new Date(minuta.approved_at).toLocaleDateString('pt-BR')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2" data-testid="grounding-confidence">
          <span>Confiança: {Math.round(minuta.grounding_confidence * 100)}%</span>
          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                minuta.grounding_confidence >= 0.8 ? 'bg-green-500' :
                minuta.grounding_confidence >= 0.6 ? 'bg-yellow-500' :
                'bg-orange-500'
              }`}
              style={{ width: `${minuta.grounding_confidence * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <EditorToolbar
        editor={editor}
        onSave={handleSave}
        onApprove={handleApproveClick}
        onReject={handleReject}
        onToggleCitations={handleToggleCitations}
        citationsVisible={citationsVisible}
        canApprove={baseCanApprove}
        isSaving={false}
      />

      {/* Override Approval Modal */}
      {showOverrideModal && (
        <OverrideApproveModal
          open={showOverrideModal}
          onOpenChange={setShowOverrideModal}
          onConfirm={handleApproveWithOverride}
          blockerCount={blockers.length}
        />
      )}

      {/* Editor Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Entities Panel */}
        <EntitiesPanel editor={editor} />

        {/* Main Editor */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-auto p-4">
            <EditorContent
              editor={editor}
              className="prose prose-lg max-w-none focus:outline-none"
              data-testid="editor-content"
            />
          </div>

          {/* Status Bar */}
          <div className="border-t border-gray-200 px-4 py-2 bg-gray-50 flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-4">
              <span data-testid="character-count">
                {editor.storage.characterCount.characters()} caracteres
              </span>
              <span>
                {editor.storage.characterCount.words()} palavras
              </span>
              {isEditing && (
                <span className="text-orange-600" data-testid="edit-confidence">
                  Editado ({Math.round(editConfidence * 100)}% preservado)
                </span>
              )}
            </div>
            
            {/* Placeholder count */}
            <div className="flex items-center gap-4">
              <span data-testid="placeholder-count">
                Placeholders: {getPlaceholders().length}
              </span>
              <span data-testid="placeholders-resolved">
                Resolvidos: 0
              </span>
            </div>
          </div>
        </div>

        {/* Right HITL Sidebar */}
        {showCitations && citationsVisible && (
          <HITLRightSidebar editor={editor} />
        )}
      </div>

      {/* Placeholder Resolution Panel */}
      {showPlaceholders && !placeholdersResolved && (
        <div className="border-t border-gray-200 p-4 bg-yellow-50">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-yellow-800">
              Placeholders PII Detectados
            </h4>
            <button
              onClick={togglePlaceholders}
              className="text-sm text-yellow-700 hover:text-yellow-900 underline"
            >
              Resolver todos
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {getPlaceholders().map((placeholder) => (
              <PlaceholderHighlight
                key={placeholder.id}
                placeholder={placeholder}
                showResolveButton={true}
                onResolve={(p) => {
                  // This would open a modal to resolve the placeholder
                  console.log('Resolve placeholder:', p);
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default HITLEditor;
