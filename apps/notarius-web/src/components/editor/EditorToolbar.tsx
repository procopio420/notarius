/**
 * Editor Toolbar Component with TipTap controls
 */

import React from 'react';
import { Editor } from '@tiptap/react';
import { 
  Bold, 
  Italic, 
  Underline, 
  Strikethrough, 
  Code, 
  Link, 
  Heading1, 
  Heading2, 
  Heading3,
  List,
  ListOrdered,
  Quote,
  Code2,
  Undo,
  Redo,
  Save,
  Check,
  X,
  Eye,
  EyeOff
} from 'lucide-react';

interface EditorToolbarProps {
  editor: Editor | null;
  onSave: () => void;
  onApprove: () => void;
  onReject: () => void;
  onToggleCitations: () => void;
  citationsVisible: boolean;
  canApprove: boolean;
  isSaving: boolean;
}

export const EditorToolbar: React.FC<EditorToolbarProps> = ({
  editor,
  onSave,
  onApprove,
  onReject,
  onToggleCitations,
  citationsVisible,
  canApprove,
  isSaving,
}) => {
  if (!editor) return null;

  const ToolbarButton: React.FC<{
    onClick: () => void;
    isActive?: boolean;
    disabled?: boolean;
    icon: React.ReactNode;
    label: string;
    shortcut?: string;
    testId?: string;
  }> = ({ onClick, isActive, disabled, icon, label, shortcut, testId }) => (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        p-2 rounded-md transition-colors
        ${isActive 
          ? 'bg-blue-100 text-blue-700' 
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      title={`${label}${shortcut ? ` (${shortcut})` : ''}`}
      data-testid={testId || `toolbar-${label.toLowerCase().replace(/\s+/g, '-')}`}
      aria-label={label}
    >
      {icon}
    </button>
  );

  return (
    <div className="border-b border-gray-200 bg-white p-2" data-testid="editor-toolbar">
      <div className="flex items-center gap-1 flex-wrap">
        {/* Text Formatting */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2 mr-2">
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBold().run()}
            isActive={editor.isActive('bold')}
            icon={<Bold size={16} />}
            label="Negrito"
            shortcut="Ctrl+B"
            testId="toolbar-bold"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleItalic().run()}
            isActive={editor.isActive('italic')}
            icon={<Italic size={16} />}
            label="Itálico"
            shortcut="Ctrl+I"
            testId="toolbar-italic"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            isActive={editor.isActive('underline')}
            icon={<Underline size={16} />}
            label="Sublinhado"
            shortcut="Ctrl+U"
            testId="toolbar-underline"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleStrike().run()}
            isActive={editor.isActive('strike')}
            icon={<Strikethrough size={16} />}
            label="Riscado"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleCode().run()}
            isActive={editor.isActive('code')}
            icon={<Code size={16} />}
            label="Código"
          />
        </div>

        {/* Headings */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2 mr-2">
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            isActive={editor.isActive('heading', { level: 1 })}
            icon={<Heading1 size={16} />}
            label="Título 1"
            testId="toolbar-heading1"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            isActive={editor.isActive('heading', { level: 2 })}
            icon={<Heading2 size={16} />}
            label="Título 2"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            isActive={editor.isActive('heading', { level: 3 })}
            icon={<Heading3 size={16} />}
            label="Título 3"
          />
        </div>

        {/* Lists */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2 mr-2">
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            isActive={editor.isActive('bulletList')}
            icon={<List size={16} />}
            label="Lista com marcadores"
            testId="toolbar-bullet-list"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            isActive={editor.isActive('orderedList')}
            icon={<ListOrdered size={16} />}
            label="Lista numerada"
            testId="toolbar-numbered-list"
          />
        </div>

        {/* Blocks */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2 mr-2">
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            isActive={editor.isActive('blockquote')}
            icon={<Quote size={16} />}
            label="Citação"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
            isActive={editor.isActive('codeBlock')}
            icon={<Code2 size={16} />}
            label="Bloco de código"
          />
        </div>

        {/* History */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2 mr-2">
          <ToolbarButton
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().undo()}
            icon={<Undo size={16} />}
            label="Desfazer"
            shortcut="Ctrl+Z"
            testId="toolbar-undo"
          />
          <ToolbarButton
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().redo()}
            icon={<Redo size={16} />}
            label="Refazer"
            shortcut="Ctrl+Y"
            testId="toolbar-redo"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 ml-auto">
          <ToolbarButton
            onClick={onToggleCitations}
            isActive={citationsVisible}
            icon={citationsVisible ? <Eye size={16} /> : <EyeOff size={16} />}
            label={citationsVisible ? "Ocultar citações" : "Mostrar citações"}
            testId="toggle-citations"
          />
          
          <ToolbarButton
            onClick={onSave}
            disabled={isSaving}
            icon={<Save size={16} />}
            label="Salvar"
            shortcut="Ctrl+S"
            testId="save-button"
          />
          
          <div className="flex items-center gap-1 border-l border-gray-200 pl-2 ml-2">
            <ToolbarButton
              onClick={onReject}
              icon={<X size={16} />}
              label="Rejeitar"
              testId="reject-button"
            />
            <ToolbarButton
              onClick={onApprove}
              disabled={!canApprove}
              icon={<Check size={16} />}
              label="Aprovar"
              testId="approve-button"
              title={canApprove ? "Aprovar" : "Aprovar (requer condições atendidas)"}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditorToolbar;
