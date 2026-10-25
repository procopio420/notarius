import { api } from './api'

export const situacoesProposta: Record<string, string> = {
  mensagem_corrigida: 'Mensagem corrigida: reveja a fonte atual',
  referencia_redacao: 'Referência de redação: não usar como dado do caso', nao_utilizar: 'Fonte não utilizada no caso',
  pendente: 'Aguardando revisão', associada: 'Associada, sem confirmação', aceita: 'Aceita pela escrevente',
  rejeitada: 'Não utilizada por decisão da escrevente', reaberta: 'Precisa de nova revisão',
  leitura_substituida: 'Leitura substituída', substituida: 'Substituída por revisão posterior do campo',
}

export interface PropostaEvidencia {
  analise_documental_id?: string | null
  evidencia_estruturada?: { associacao?: string; registro_sugerido_id?: string | null; relacionado_id?: string | null; contexto?: string }
  id: string; rotulo: string; valor_original: string; trecho: string; destinos: { tipo: string; chave: string; rotulo: string }[]
  origem: { tipo: 'documento' | 'mensagem'; pagina_id?: string; mensagem_id?: string; anexo_id?: string; arquivo?: string; pagina: number | null; leitura_versao: number | null; leitura_situacao?: string; leitura_aviso?: string; canal: 'texto' | 'ocr'; linha: number; metodo: string }
  situacao: string; fonte_atual: boolean; versao_decisao: number; confirmado: boolean
  decisoes: { id: string; versao: number; acao: string; objeto_id: string | null; revisao_id: string | null; autor_id: string; autor_nome: string; data: string; justificativa: string }[]
}
export interface ExtracaoPropostas { propostas_ids: string[]; linhas_nao_interpretadas: number; problemas_leitura: string[]; modo: 'simulacao_local'; aviso: string }
export const propostasDadosApi = {
  fonte: async (id: string, proposta: string): Promise<{ texto: string; trecho: string; origem: PropostaEvidencia['origem']; fonte_atual: boolean }> =>
    (await api.get(`/atendimentos/${id}/propostas-dados/${proposta}/fonte/`)).data,
  get: async (id: string): Promise<{ propostas: PropostaEvidencia[] }> => (await api.get(`/atendimentos/${id}/propostas-dados/`)).data,
  extrair: async (id: string, source: { anexo_id?: string; leitura_versao?: number; mensagem_id?: string }, client_id: string): Promise<ExtracaoPropostas> =>
    (await api.post(`/atendimentos/${id}/propostas-dados/`, { operacao: 'extrair', ...source, client_id })).data,
  rejeitar: async (id: string, data: { proposta_id: string; versao_esperada: number; justificativa: string; client_id: string }) =>
    (await api.post(`/atendimentos/${id}/propostas-dados/`, { operacao: 'rejeitar', ...data })).data,
}
