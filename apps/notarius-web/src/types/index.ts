// Base types
export interface BaseModel {
  id: string
  created_at: string
  updated_at: string
}

export interface Tenant extends BaseModel {
  nome: string
  uf: string
  municipio?: string
  tipo?: string
  settings: Record<string, unknown>
}

export interface TenantSearchResult {
  id: string
  nome: string
  municipio: string
  uf: string
  tipo: string
}

export interface TenantRequest {
  nome: string
  municipio: string
  uf: string
  note?: string
}

export interface RegisterResponse {
  status: 'ACTIVE' | 'NO_CARTORIO'
  redirect: string
  token: string
  user: User
}

export interface User extends BaseModel {
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
}

// Document types
export interface Documento extends BaseModel {
  tenant: string
  tipo: string
  processo: string
  s3_key?: string
  hash_sha256?: string
  mime?: string
  pages?: number
  status: 'uploaded' | 'processing' | 'ready' | 'signed' | 'archived'
  ocr_text?: string
  ocr_meta?: Record<string, unknown>
}

export interface Minuta extends BaseModel {
  tenant: string
  processo: string
  versao: number
  gerada_por: 'manual' | 'ai' | 'template'
  template_id?: string
  corpo_md: string
  variaveis_json?: Record<string, unknown>
  created_by: string
}

export interface Template extends BaseModel {
  tenant: string
  nome: string
  categoria: string
  corpo_template: string
  schema_variaveis: Record<string, any>
  is_active: boolean
  version: number
  created_by: string
}

// AI types
export interface AIGeneratedMinuta extends BaseModel {
  tenant: string
  minuta: string
  original_command: string
  parsed_intent: Record<string, any>
  ai_model_version: string
  generation_timestamp: string
  confidence_score: number
  reviewed_by?: string
  approved: boolean
  edited_after_generation: boolean
  clauses_used: string[]
  generation_time_ms: number
}

export interface ClauseLibrary extends BaseModel {
  tenant: string
  categoria: string
  nome: string
  texto: string
  condicoes: Record<string, any>
  frequencia_uso: number
  is_active: boolean
  created_by: string
}

// Workflow types
export interface WorkflowTask extends BaseModel {
  tenant: string
  titulo: string
  descricao: string
  tipo: 'autenticacao' | 'assinatura' | 'revisao' | 'aprovacao' | 'protocolo' | 'outro'
  prioridade: 'baixa' | 'media' | 'alta' | 'urgente'
  status: 'pendente' | 'em_andamento' | 'concluida' | 'cancelada'
  documento?: string
  minuta?: string
  processo?: string
  assigned_to?: string
  created_by: string
  deadline?: string
  completed_at?: string
  metadata: Record<string, any>
}

export interface DocumentoNota extends BaseModel {
  tenant: string
  documento: string
  titulo: string
  conteudo: string
  is_private: boolean
  is_resolved: boolean
  created_by: string
}

// Signature types
export interface AssinaturaFluxo extends BaseModel {
  tenant: string
  minuta: string
  status: 'rascunho' | 'pendente' | 'em_andamento' | 'concluido' | 'cancelado'
  tipo_certificado: 'A1' | 'A3'
  deadline?: string
  observacoes?: string
}

export interface AssinaturaItem extends BaseModel {
  tenant: string
  fluxo: string
  signatario_nome: string
  signatario_cpf_hash?: string
  signatario_email?: string
  ordem: number
  papel: 'outorgante' | 'outorgado' | 'testemunha' | 'tabeliao'
  status: 'pendente' | 'assinado' | 'recusado'
  assinado_em?: string
  certificado_serial?: string
  certificado_validade?: string
  assinatura_hash?: string
}

// Notification types
export interface NotificationTemplate extends BaseModel {
  tenant: string
  nome: string
  tipo: 'email' | 'sms' | 'whatsapp' | 'push'
  trigger: 'documento_ready' | 'assinatura_pending' | 'assinatura_completed' | 'task_assigned' | 'deadline_approaching' | 'custom'
  assunto: string
  corpo: string
  is_active: boolean
  created_by: string
}

export interface NotificationLog extends BaseModel {
  tenant: string
  template: string
  recipient_email: string
  recipient_phone: string
  recipient_name: string
  documento?: string
  minuta?: string
  task?: string
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced'
  sent_at?: string
  delivered_at?: string
  error_message?: string
  rendered_subject: string
  rendered_body: string
  metadata: Record<string, any>
}

// Process types
export interface Processo extends BaseModel {
  tenant: string
  tipo_ato: string
  status: 'rascunho' | 'em_andamento' | 'concluido' | 'cancelado'
  metadados: Record<string, any>
}

export interface Protocolo extends BaseModel {
  tenant: string
  numero: number
  ano: number
  tipo: 'entrada' | 'saida'
  processo: string
  created_by: string
}

// Part types
export interface Parte extends BaseModel {
  tenant: string
  nome: string
  tipo: 'pessoa_fisica' | 'pessoa_juridica'
  cpf_cnpj: string
  email?: string
  telefone?: string
  endereco?: Record<string, any>
  metadados: Record<string, any>
}

// Financial types
export interface FinanceiroItem extends BaseModel {
  tenant: string
  processo: string
  tipo: 'receita' | 'despesa'
  categoria: string
  descricao: string
  valor: number
  data_vencimento?: string
  data_pagamento?: string
  status: 'pendente' | 'pago' | 'vencido' | 'cancelado'
  metadados: Record<string, any>
}

// Analytics types
export interface AIUsageAnalytics extends BaseModel {
  tenant: string
  command_length: number
  generation_time_ms: number
  confidence_score: number
  approved: boolean
  edited_after_generation: boolean
  document_type: string
  clauses_count: number
  ai_model_version: string
}

// API Response types
export interface ApiResponse<T> {
  count: number
  next?: string
  previous?: string
  results: T[]
}

export interface ApiError {
  detail?: string
  message?: string
  errors?: Record<string, string[]>
}

// Form types
export interface AICommandForm {
  command: string
  processo_id: string
  auto_approve?: boolean
  create_signature_workflow?: boolean
  tipo_certificado?: 'A1' | 'A3'
  deadline_days?: number
  signatarios?: Array<{
    nome: string
    email: string
    papel: 'outorgante' | 'outorgado' | 'testemunha'
  }>
}

export interface TaskForm {
  titulo: string
  descricao: string
  tipo: WorkflowTask['tipo']
  prioridade: WorkflowTask['prioridade']
  assigned_to?: string
  deadline?: string
  documento?: string
  minuta?: string
  processo?: string
}

export interface NotificationTemplateForm {
  nome: string
  tipo: NotificationTemplate['tipo']
  trigger: NotificationTemplate['trigger']
  assunto: string
  corpo: string
  is_active: boolean
}

// Dashboard types
export interface DashboardStats {
  total_documents: number
  pending_signatures: number
  completed_today: number
  ai_generations: number
  approval_rate: number
  avg_confidence: number
}

export interface TaskDashboard {
  pending_tasks: WorkflowTask[]
  in_progress_tasks: WorkflowTask[]
  overdue_tasks: WorkflowTask[]
  upcoming_tasks: WorkflowTask[]
  recent_completed: WorkflowTask[]
  summary: {
    total_pending: number
    total_in_progress: number
    total_overdue: number
    total_upcoming: number
    total_recent_completed: number
  }
}
