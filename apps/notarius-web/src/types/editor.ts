/**
 * Types for the HITL Editor system
 */

export interface Citation {
  id: string;
  uri: string;
  anchor: string;
  title: string;
  effective_date: string;
  status: 'active' | 'revoked' | 'superseded';
  snippet: string;
  confidence: number;
}

export interface Minuta {
  id: string;
  versao: number;
  status: 'rascunho' | 'processando' | 'pronto' | 'aprovado' | 'finalizado' | 'erro' | 'cancelado';
  gerada_por: 'humano' | 'ia';
  corpo_md: string;
  variaveis_json: Record<string, string>;
  citations: Citation[];
  grounding_confidence: number;
  lexnode_trace: Record<string, any>;
  skeleton_cache_key: string;
  template_version: string;
  created_by: string;
  approved_by?: string;
  approved_at?: string;
  finalized_at?: string;
  final_document?: string;
}

export interface Change {
  id: string;
  type: 'insert' | 'delete' | 'replace';
  from: number;
  to: number;
  text: string;
  timestamp: Date;
  user_id: string;
}

export interface EditorState {
  minuta: Minuta;
  originalDraft: string;
  currentContent: string;
  changes: Change[];
  citationsVisible: boolean;
  placeholdersResolved: boolean;
  isEditing: boolean;
  editConfidence: number;
  // HITL state
  entityLinks: EntityLink[];
  groundingLinks: GroundingLink[];
  suggestions: Suggestion[];
  issues: Issue[];
  auditEvents: AuditEvent[];
  revealedPII: Map<string, { value: string; reason: string; timestamp: Date }>;
}

export interface Placeholder {
  id: string;
  type: 'name' | 'cpf' | 'cnpj' | 'address' | 'phone' | 'email';
  token: string;
  displayText: string;
  position: number;
  length: number;
}

export interface Entity extends Placeholder {
  label: string;
  scope: string;
  lastUsedAt?: Date;
}

export interface EntityLink {
  entityId: string;
  from: number;
  to: number;
}

export interface GroundingLink {
  citationId: string;
  from: number;
  to: number;
}

export interface Suggestion {
  id: string;
  kind: 'INSERT' | 'REPLACE' | 'REMOVE';
  confidence: number;
  tags: string[];
  targetRange: {
    from: number;
    to: number;
  };
  beforeText: string;
  afterText: string;
}

export interface Issue {
  id: string;
  severity: 'Bloqueador' | 'Alerta' | 'Informativo';
  message: string;
  rule?: string;
}

export interface AuditEvent {
  id: string;
  action: 'PII_REVEALED' | 'ENTITY_LINKED' | 'CITATION_ATTACHED' | 'SUGGESTION_APPLIED' | 'SUGGESTION_REJECTED' | 'CHECKS_RUN' | 'APPROVED_WITH_OVERRIDE' | 'APPROVED' | 'REJECTED';
  entityId?: string;
  citationId?: string;
  suggestionId?: string;
  reason?: string;
  timestamp: Date;
}

export interface Clause {
  id: string;
  nome: string;
  texto: string;
  categoria: string;
  frequencia_uso: number;
  is_active: boolean;
}

export interface EditorToolbarAction {
  type: 'bold' | 'italic' | 'underline' | 'strike' | 'code' | 'link' | 'heading' | 'bulletList' | 'orderedList' | 'blockquote' | 'codeBlock' | 'undo' | 'redo' | 'save' | 'approve' | 'reject';
  icon: string;
  label: string;
  shortcut?: string;
  disabled?: boolean;
}

export interface CitationTooltipProps {
  citation: Citation;
  children: React.ReactNode;
}

export interface EditorProps {
  minuta: Minuta;
  onSave: (content: string) => void;
  onApprove: () => void;
  onReject: () => void;
  onExplainClause: (clauseId: string) => void;
  readOnly?: boolean;
  showCitations?: boolean;
  showPlaceholders?: boolean;
}
