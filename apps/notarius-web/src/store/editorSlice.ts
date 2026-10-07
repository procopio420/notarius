/**
 * Zustand store for HITL Editor state management
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Minuta, Change, EditorState, Placeholder, Entity, EntityLink, GroundingLink, Suggestion, Issue, AuditEvent } from '../types/editor';
import { loadHITLState, saveHITLState } from '../lib/hitl/storage';
import { generateMockSuggestions } from '../lib/hitl/mock';
import { Editor } from '@tiptap/react';

interface EditorStore extends EditorState {
  // Actions
  setMinuta: (minuta: Minuta) => void;
  updateContent: (content: string) => void;
  trackChange: (change: Change) => void;
  toggleCitations: () => void;
  togglePlaceholders: () => void;
  setEditing: (isEditing: boolean) => void;
  resetEditor: () => void;
  calculateEditConfidence: () => void;
  
  // HITL Actions
  addEntityLink: (entityId: string, from: number, to: number) => void;
  addGroundingLink: (citationId: string, from: number, to: number) => void;
  applySuggestion: (suggestionId: string, editor: Editor | null) => void;
  rejectSuggestion: (suggestionId: string) => void;
  revealPII: (entityId: string, value: string, reason: string) => void;
  logAuditEvent: (event: Omit<AuditEvent, 'id' | 'timestamp'>) => void;
  runChecks: () => Issue[];
  loadHITLState: (minutaId: string) => void;
  saveHITLState: (minutaId: string) => void;
  getEntities: () => Entity[];
  
  // Computed values
  getPlaceholders: () => Placeholder[];
  getChangesCount: () => number;
  getEditDistance: () => number;
}

const initialState: EditorState = {
  minuta: {} as Minuta,
  originalDraft: '',
  currentContent: '',
  changes: [],
  citationsVisible: true,
  placeholdersResolved: false,
  isEditing: false,
  editConfidence: 1.0,
  // HITL state
  entityLinks: [],
  groundingLinks: [],
  suggestions: [],
  issues: [],
  auditEvents: [],
  revealedPII: new Map(),
};

export const useEditorStore = create<EditorStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setMinuta: (minuta: Minuta) => {
        set({
          minuta,
          originalDraft: minuta.corpo_md,
          currentContent: minuta.corpo_md,
          changes: [],
          editConfidence: 1.0,
        });
        // Load HITL state for this minuta
        get().loadHITLState(minuta.id);
      },

      updateContent: (content: string) => {
        const { currentContent, changes } = get();
        
        // Calculate diff between old and new content
        const diff = calculateDiff(currentContent, content);
        
        // Create change record
        const change: Change = {
          id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          type: diff.type,
          from: diff.from,
          to: diff.to,
          text: diff.text,
          timestamp: new Date(),
          user_id: 'current_user', // This would come from auth context
        };

        set({
          currentContent: content,
          changes: [...changes, change],
          isEditing: true,
        });

        // Recalculate edit confidence
        get().calculateEditConfidence();
      },

      trackChange: (change: Change) => {
        set((state) => ({
          changes: [...state.changes, change],
        }));
        get().calculateEditConfidence();
      },

      toggleCitations: () => {
        set((state) => ({
          citationsVisible: !state.citationsVisible,
        }));
      },

      togglePlaceholders: () => {
        set((state) => ({
          placeholdersResolved: !state.placeholdersResolved,
        }));
      },

      setEditing: (isEditing: boolean) => {
        set({ isEditing });
      },

      resetEditor: () => {
        set({
          ...initialState,
          revealedPII: new Map(), // Create new Map instance
        });
      },

      calculateEditConfidence: () => {
        const { originalDraft, currentContent } = get();
        const editDistance = get().getEditDistance();
        const maxLength = Math.max(originalDraft.length, currentContent.length);
        
        // Calculate confidence based on how much was preserved
        const confidence = maxLength > 0 ? 1 - (editDistance / maxLength) : 1;
        
        set({ editConfidence: Math.max(0, Math.min(1, confidence)) });
      },

      getPlaceholders: () => {
        const { currentContent } = get();
        const placeholderRegex = /\{\{([^}]+)\}\}/g;
        const placeholders: Placeholder[] = [];
        let match;

        while ((match = placeholderRegex.exec(currentContent)) !== null) {
          const fullMatch = match[0];
          const placeholderText = match[1];
          
          // Parse placeholder type and token
          const [type, token] = placeholderText.split('_');
          
          placeholders.push({
            id: `placeholder_${match.index}`,
            type: type.toLowerCase() as Placeholder['type'],
            token: fullMatch,
            displayText: fullMatch,
            position: match.index,
            length: fullMatch.length,
          });
        }

        return placeholders;
      },

      getChangesCount: () => {
        return get().changes.length;
      },

      getEditDistance: () => {
        const { originalDraft, currentContent } = get();
        return levenshteinDistance(originalDraft, currentContent);
      },

      // HITL Actions
      addEntityLink: (entityId: string, from: number, to: number) => {
        const link: EntityLink = { entityId, from, to };
        set((state) => ({
          entityLinks: [...state.entityLinks, link],
        }));
        get().logAuditEvent({
          action: 'ENTITY_LINKED',
          entityId,
        });
        // Auto-save HITL state
        const { minuta } = get();
        if (minuta.id) {
          get().saveHITLState(minuta.id);
        }
      },

      addGroundingLink: (citationId: string, from: number, to: number) => {
        const link: GroundingLink = { citationId, from, to };
        set((state) => ({
          groundingLinks: [...state.groundingLinks, link],
        }));
        get().logAuditEvent({
          action: 'CITATION_ATTACHED',
          citationId,
        });
        // Auto-save HITL state
        const { minuta } = get();
        if (minuta.id) {
          get().saveHITLState(minuta.id);
        }
      },

      applySuggestion: (suggestionId: string, editor: Editor | null) => {
        const { suggestions } = get();
        const suggestion = suggestions.find((s) => s.id === suggestionId);
        if (!suggestion || !editor) {
          return;
        }

        // Apply suggestion using TipTap transaction
        const { from, to } = suggestion.targetRange;
        if (suggestion.kind === 'INSERT') {
          editor.chain().focus().insertContentAt(from, suggestion.afterText).run();
        } else if (suggestion.kind === 'REPLACE') {
          editor.chain().focus().setTextSelection({ from, to }).insertContent(suggestion.afterText).run();
        } else if (suggestion.kind === 'REMOVE') {
          editor.chain().focus().setTextSelection({ from, to }).deleteSelection().run();
        }

        // Remove suggestion from list
        set((state) => ({
          suggestions: state.suggestions.filter((s) => s.id !== suggestionId),
        }));

        get().logAuditEvent({
          action: 'SUGGESTION_APPLIED',
          suggestionId,
        });

        // Auto-save HITL state
        const { minuta } = get();
        if (minuta.id) {
          get().saveHITLState(minuta.id);
        }
      },

      rejectSuggestion: (suggestionId: string) => {
        set((state) => ({
          suggestions: state.suggestions.filter((s) => s.id !== suggestionId),
        }));

        get().logAuditEvent({
          action: 'SUGGESTION_REJECTED',
          suggestionId,
        });

        // Auto-save HITL state
        const { minuta } = get();
        if (minuta.id) {
          get().saveHITLState(minuta.id);
        }
      },

      revealPII: (entityId: string, value: string, reason: string) => {
        const { revealedPII } = get();
        const newMap = new Map(revealedPII);
        newMap.set(entityId, {
          value,
          reason,
          timestamp: new Date(),
        });

        set({ revealedPII: newMap });

        get().logAuditEvent({
          action: 'PII_REVEALED',
          entityId,
          reason,
        });

        // Note: revealedPII is NOT persisted to localStorage (privacy requirement)
      },

      logAuditEvent: (event: Omit<AuditEvent, 'id' | 'timestamp'>) => {
        const auditEvent: AuditEvent = {
          id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          ...event,
          timestamp: new Date(),
        };

        set((state) => ({
          auditEvents: [auditEvent, ...state.auditEvents].slice(0, 100), // Keep last 100 events
        }));

        // Auto-save HITL state (excluding revealedPII)
        const { minuta } = get();
        if (minuta.id) {
          get().saveHITLState(minuta.id);
        }
      },

      runChecks: () => {
        const { currentContent, minuta, editConfidence, groundingLinks } = get();
        const issues: Issue[] = [];

        // Check 1: Missing required content
        if (currentContent.length < 100) {
          issues.push({
            id: `issue_${Date.now()}_1`,
            severity: 'Bloqueador',
            message: 'Documento muito curto. Mínimo de 100 caracteres necessário.',
            rule: 'MIN_LENGTH',
          });
        }

        // Check 2: Low edit confidence
        if (editConfidence < 0.5) {
          issues.push({
            id: `issue_${Date.now()}_2`,
            severity: 'Alerta',
            message: `Confiança de edição baixa (${Math.round(editConfidence * 100)}%). Verifique as alterações.`,
            rule: 'EDIT_CONFIDENCE',
          });
        }

        // Check 3: Low grounding coverage
        const totalLength = currentContent.length;
        if (totalLength > 0) {
          let coveredLength = 0;
          groundingLinks.forEach((link) => {
            coveredLength += Math.max(0, link.to - link.from);
          });
          const coverage = coveredLength / totalLength;
          if (coverage < 0.3) {
            issues.push({
              id: `issue_${Date.now()}_3`,
              severity: 'Alerta',
              message: `Cobertura de fundamentação baixa (${Math.round(coverage * 100)}%). Considere adicionar mais citações.`,
              rule: 'GROUNDING_COVERAGE',
            });
          }
        }

        // Check 4: Missing citations
        if (minuta.citations && minuta.citations.length === 0) {
          issues.push({
            id: `issue_${Date.now()}_4`,
            severity: 'Informativo',
            message: 'Nenhuma citação legal encontrada. Considere adicionar fundamentação.',
            rule: 'CITATIONS',
          });
        }

        // Check 5: Status not ready
        if (minuta.status !== 'pronto') {
          issues.push({
            id: `issue_${Date.now()}_5`,
            severity: 'Bloqueador',
            message: `Documento não está pronto para aprovação. Status atual: ${minuta.status}`,
            rule: 'STATUS',
          });
        }

        set({ issues });
        get().logAuditEvent({
          action: 'CHECKS_RUN',
        });

        return issues;
      },

      loadHITLState: (minutaId: string) => {
        const loaded = loadHITLState(minutaId);
        if (loaded) {
          set({
            entityLinks: loaded.entityLinks || [],
            groundingLinks: loaded.groundingLinks || [],
            suggestions: loaded.suggestions || [],
            issues: loaded.issues || [],
            auditEvents: loaded.auditEvents || [],
            // Note: revealedPII is NOT loaded (privacy requirement)
          });
        } else {
          // Initialize with empty state
          set({
            entityLinks: [],
            groundingLinks: [],
            suggestions: [],
            issues: [],
            auditEvents: [],
          });
        }

        // Generate mock suggestions if none exist
        const { currentContent, suggestions } = get();
        if (suggestions.length === 0 && currentContent) {
          const mockSuggestions = generateMockSuggestions(currentContent);
          set({ suggestions: mockSuggestions });
        }
      },

      saveHITLState: (minutaId: string) => {
        const { entityLinks, groundingLinks, suggestions, issues, auditEvents } = get();
        saveHITLState(minutaId, {
          entityLinks,
          groundingLinks,
          suggestions,
          issues,
          auditEvents,
          // Note: revealedPII is NOT saved (privacy requirement)
        });
      },

      getEntities: () => {
        const { getPlaceholders } = get();
        const placeholders = getPlaceholders();
        
        // Convert placeholders to entities with enriched metadata
        const entities: Entity[] = placeholders.map((placeholder) => {
          const typeMap: Record<string, string> = {
            name: 'NOME',
            cpf: 'CPF',
            cnpj: 'CNPJ',
            address: 'ENDEREÇO',
            phone: 'TELEFONE',
            email: 'EMAIL',
          };

          return {
            ...placeholder,
            label: typeMap[placeholder.type] || placeholder.type.toUpperCase(),
            scope: 'Documento inteiro',
            lastUsedAt: new Date(),
          };
        });

        return entities;
      },
    }),
    {
      name: 'editor-store',
    }
  )
);

// Helper functions
function calculateDiff(oldText: string, newText: string) {
  const oldLength = oldText.length;
  const newLength = newText.length;
  
  if (newLength > oldLength) {
    // Text was inserted
    return {
      type: 'insert' as const,
      from: oldLength,
      to: newLength,
      text: newText.slice(oldLength),
    };
  } else if (newLength < oldLength) {
    // Text was deleted
    return {
      type: 'delete' as const,
      from: newLength,
      to: oldLength,
      text: oldText.slice(newLength),
    };
  } else {
    // Text was replaced
    return {
      type: 'replace' as const,
      from: 0,
      to: newLength,
      text: newText,
    };
  }
}

function levenshteinDistance(str1: string, str2: string): number {
  const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));

  for (let i = 0; i <= str1.length; i++) {
    matrix[0][i] = i;
  }

  for (let j = 0; j <= str2.length; j++) {
    matrix[j][0] = j;
  }

  for (let j = 1; j <= str2.length; j++) {
    for (let i = 1; i <= str1.length; i++) {
      const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[j][i] = Math.min(
        matrix[j][i - 1] + 1, // deletion
        matrix[j - 1][i] + 1, // insertion
        matrix[j - 1][i - 1] + indicator // substitution
      );
    }
  }

  return matrix[str2.length][str1.length];
}
