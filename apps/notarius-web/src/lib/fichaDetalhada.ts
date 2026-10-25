import { api } from './api'
import type { RevisaoDado, SituacaoDado } from './atendimentos'
import type { PropostaEvidencia } from './propostasDados'

export type TipoRegistro = 'pessoa' | 'papel' | 'relacao' | 'imovel' | 'negociacao' | 'ato' | 'complemento'
export type SituacaoDetalhada = SituacaoDado | 'extraido'
export interface CampoDetalhado { chave: string; rotulo: string; grupo: string; contexto_assinatura: string; opcoes?: string[]; atual: RevisaoDetalhada | null; historico: RevisaoDetalhada[] }
export interface RevisaoDetalhada extends Omit<RevisaoDado, 'situacao' | 'origem'> {
  situacao: SituacaoDetalhada; valor_original: string; rotulo_original: string; fonte_atual: boolean
  natureza_origem: string; confirmacao: { autor_id: string; autor_nome: string; data: string } | null
  confirmacao_atual: boolean; situacao_efetiva: string; dependencias_atuais: boolean
  propostas_ids: string[]
  origem: { tipo: string; mensagem_id?: string | null; pagina_id?: string; revisao_id?: string; trecho?: string; canal?: 'texto' | 'ocr'; leitura_versao?: number; arquivo?: string; pagina?: number; versao?: number }
  validacao_formato?: { formato_consistente: boolean; digitos_consistentes: boolean; identidade_comprovada: false; aviso: string }
}
export interface RegistroFicha { rotulo?: string; id: string; tipo: TipoRegistro; pessoa_a_id: string | null; pessoa_b_id: string | null; imovel_id: string | null; campos: CampoDetalhado[]; criacao: { autor_id: string; autor_nome: string; data: string; motivo: string } }
export interface FichaDetalhadaData { objetos: RegistroFicha[]; legado: RevisaoDetalhada[]; propostas: PropostaEvidencia[]; schema: Record<TipoRegistro, Omit<CampoDetalhado, 'atual' | 'historico' | 'contexto_assinatura'>[]>; modelo_id: string | null; aviso: string }
export const fichaDetalhadaApi = {
  get: async (id: string): Promise<FichaDetalhadaData> => (await api.get(`/atendimentos/${id}/ficha-detalhada/`)).data,
  alterar: async (id: string, data: object): Promise<{ objeto_id: string; revisoes: string[] }> => (await api.post(`/atendimentos/${id}/ficha-detalhada/`, data)).data,
}
