import { api } from './api'

export interface Atendimento {
  id: string
  titulo: string
  tipo_ato: string
  created_at: string
  updated_at: string
  situacao: 'em_andamento' | 'aguardando' | 'pausado'
  versao_cadastro: number
}

export interface Mensagem {
  correcao_de?: string | null; motivo_correcao?: string
  id: string
  client_id: string
  texto: string
  autor_nome: string
  created_at: string
  campo?: string; pergunta?: string
}
export interface FeedbackTeste {
  id: string; client_id: string; etapa: string; tipo: string; descricao: string; esperado: string
  autor_nome: string; created_at: string
  contexto: { assinatura_dados: string; modelo_versao: number | null; minuta_versao: number | null; pendencias: number }
}

export interface PerguntaConferencia {
  destino?: { registro_rotulo?: string; pendencia_id?: string; subtipo?: string; objeto_id?: string | null; campo?: string; proposta_id?: string | null; mensagem_id?: string | null; pagina_id?: string | null; anexo_id?: string | null; trecho?: string | null; tarefa?: string }
  chave: string; tipo: 'anexar' | 'documento' | 'mensagem' | 'estrutura' | 'pendencia_ficha' | 'organizacao_documento' | 'vinculacao_minuta' | 'divergencia' | 'leitura' | 'confirmacao'; rotulo: string
  assinatura: string; pergunta: string; atual: string | null; versao: number
  candidatos: { valor: string; origem: string; id: string; trecho: string; arquivo?: string; pagina?: number; canal?: string; leitura_versao?: number; situacao?: 'extraido' | 'informado' }[]
}
export interface Conferencia { pendencias: PerguntaConferencia[]; bloqueado: boolean; pode_redigir: boolean; mensagem: string; limite: string
  orientacao: { modo: string; texto: string; mensagem_id: string | null; identificados: { chave: string; rotulo: string; valor: string; trecho: string }[]; nao_interpretados: string[]; proxima_chave: string | null; limite: string }
}
export interface PedidoFicha { token: string; objeto_id?: string; campo?: string; proposta_id?: string; novo_participante?: boolean }
export interface PedidoDocumento { token: string; anexo_id: string; pagina_id?: string; acao: 'organizacao' | 'leitura' }
export interface RoteiroConversa extends Conferencia {
  modo: string; recebido: { mensagens: number; documentos: number; propostas: number; pessoas: number; imoveis: number;
    arquivos: { id: string; nome: string; leitura_versao: number; situacao_leitura: string; finalidade: string }[] }
  pendencias: PerguntaConferencia[]; total_pendencias: number; proxima: PerguntaConferencia | null; bloqueado: boolean; pode_redigir: boolean; aviso: string
}
export interface RespostaConferencia { chave: string; assinatura: string; versao_esperada: number; client_id: string; valor: string; confirmar: boolean; justificativa: string }
export interface CampoQualificacao { chave: string; rotulo: string; grupo: 'Identificação' | 'Qualificação' | 'Contato' }
export interface PosicaoMinuta { chave: string; rotulo: string; tipo: 'pessoa' | 'papel' | 'relacao' | 'imovel' | 'negociacao' | 'ato' | 'complemento'; categoria?: string; vinculos: Record<string, string> }
export interface TextoModelo { corpo: string; representacao: string; observacoes: string; registros_minuta?: PosicaoMinuta[]; campos_qualificacao?: CampoQualificacao[]; campos_obrigatorios_ficha?: { tipo: string; chave: string }[]; dependencias_campos_ficha?: { tipo: string; chave: string; depende_de: string[] }[] }
export interface ModeloMinuta extends TextoModelo { id: string; versao: number; aprovado: boolean; justificativa: string; created_at: string; referencia_id?: string | null }
export interface ModeloBiblioteca extends TextoModelo { id: string; nome: string; origem_versao: number; created_at: string; autor_nome: string }
export interface RevisaoFinal { id: string; autor_nome: string; created_at: string; motivo: string; texto_corresponde: boolean }
export interface MinutaPreparada { id: string; versao: number; corpo: string; modelo_versao: number; created_at: string; desatualizada: boolean; tipo: string; motivo: string; autor_nome: string; base_id: string | null; revisao_final: RevisaoFinal | null; ocorrencias_correspondem_texto?: boolean; dados: Record<string, { valor: string; revisao_id: string; versao: number; situacao: string; origem?: RevisaoDado['origem']; objeto_id?: string; tipo?: string; valor_original?: string; vinculacao_id?: string; decisoes_blocos?: { chave: string; incluido: boolean; valor_confirmado: string; modelo_versao: number; configuracao: { campo: string; permitidos: string[]; incluir: string[] } }[]; ocorrencias?: { bloco: string; inicio: number; fim: number; repeticao?: { bloco: string; posicao: string; indice: number }; condicional?: string }[] }> }
export interface EstadoRedacao { assinatura: string; pronto: boolean; motivo_bloqueio: string; pendencias: number; modelo_aprovado: boolean; versoes: MinutaPreparada[] }
export interface ComparacaoMinutas {
  base: { id: string; versao: number; modelo_versao: number }; destino: { id: string; versao: number; modelo_versao: number }
  texto_alterado: boolean; trechos: { tipo: 'igual' | 'removido' | 'adicionado'; texto: string }[]
  dados_alterados: { chave: string; rotulo: string; antes: MinutaPreparada['dados'][string] | null; depois: MinutaPreparada['dados'][string] | null; valor_alterado: boolean }[]
  comparacao_simplificada: boolean; aviso: string
}

export type SituacaoDado = 'ausente' | 'informado' | 'confirmado' | 'divergente' | 'ilegivel'
export interface RevisaoDado {
  id: string; chave: string; valor: string; situacao: SituacaoDado; versao: number
  justificativa: string; autor_nome: string; created_at: string
  origem: { tipo: 'manual' | 'mensagem' | 'documento'; mensagem_id: string | null; trecho: string | null; pagina_id?: string; arquivo?: string; pagina?: number; anexo_id?: string; canal?: 'texto' | 'ocr'; leitura_versao?: number; organizacao_versao?: number }
}
export interface CampoFicha {
  chave: string; rotulo: string; obrigatorio: boolean; atual: RevisaoDado | null; historico: RevisaoDado[]
}
export interface ResumoRevisao {
  gerado_em: string; assinatura: string; atendimento: Atendimento; campos: Omit<CampoFicha, 'historico'>[]
  documentos: { id: string; nome: string; situacao_leitura: string; aviso: string; leitura_versao: number; paginas: number; paginas_ocr: number; revisao_manual: { autor_nome: string; created_at: string; justificativa: string } | null }[]
  pendencias: PerguntaConferencia[]; pronto_para_preparar: boolean; motivo_bloqueio: string
  modelo: { id: string; versao: number; aprovado: boolean } | null
  minuta: { id: string; versao: number; tipo: string; desatualizada: boolean; revisao_final: RevisaoFinal | null } | null
  aviso: string
}
export interface AtualizarDado {
  chave: string; valor: string; situacao: SituacaoDado; versao_esperada: number
  justificativa: string; mensagem_id: string | null
  organizacao_versao?: number; pagina_id?: string | null; trecho_origem?: string
  canal_origem?: 'texto' | 'ocr'
}

export interface PaginaAnexo { limites_leitura?: string[]; id: string; numero: number; texto: string; situacao: string; aviso: string; metodo: string; texto_ocr: string; regioes_ocr: { texto: string; x: number; y: number; largura: number; altura: number }[]; largura_imagem: number; altura_imagem: number; ocr_idioma: string }
export interface OrganizacaoDocumento { id: string | null; versao: number; finalidade: string; tipo_documento: string; vinculos: { objeto_id: string | null; paginas: number[] }[]; leitura_versao: number | null; leitura_atual: boolean; autor: string | null; motivo: string; data: string | null }
export interface Anexo { id: string; nome: string; mime: string; tamanho: number; situacao: string; aviso: string; created_at: string; paginas: PaginaAnexo[]; leitura_versao: number; organizacao: OrganizacaoDocumento; cobertura: { total_paginas?: number | null; paginas_processadas: number; paginas_sem_texto: number[]; paginas_incertas: number[]; limites?: string[]; aviso: string } }
export interface FonteDocumento { organizacao_versao?: number; pagina_id: string; arquivo: string; pagina: number; trecho: string; canal?: 'texto' | 'ocr' }

export const atendimentosApi = {
  roteiro: async (id: string): Promise<RoteiroConversa> => (await api.get(`/atendimentos/${id}/roteiro-conversa/`)).data,
  corrigirMensagem: async (id: string, mensagem: string, data: { texto: string; justificativa: string; client_id: string }): Promise<Mensagem> => (await api.post(`/atendimentos/${id}/mensagens/${mensagem}/corrigir/`, data)).data,
  feedbacks: async (id: string): Promise<FeedbackTeste[]> => (await api.get(`/atendimentos/${id}/feedbacks-teste/`, { timeout: 15000 })).data,
  registrarFeedback: async (id: string, data: { client_id: string; etapa: string; tipo: string; descricao: string; esperado: string }): Promise<FeedbackTeste> =>
    (await api.post(`/atendimentos/${id}/feedbacks-teste/`, data, { timeout: 15000 })).data,
  revisarMinuta: async (id: string, minuta: string, versao_esperada: number, motivo: string): Promise<RevisaoFinal> =>
    (await api.post(`/atendimentos/${id}/minutas/${minuta}/revisar/`, { versao_esperada, motivo, conferi_texto: true, conferi_dados: true, conferi_fontes: true }, { timeout: 15000 })).data,
  resumoRevisao: async (id: string): Promise<ResumoRevisao> => (await api.get(`/atendimentos/${id}/resumo-revisao/`, { timeout: 15000 })).data,
  organizar: async (id: string, data: { titulo: string; situacao: Atendimento['situacao']; motivo: string; versao_esperada: number }): Promise<Atendimento> =>
    (await api.post(`/atendimentos/${id}/organizacao/`, data, { timeout: 15000 })).data,
  historicoOrganizacao: async (id: string): Promise<{ historico: { versao: number; titulo_anterior: string; titulo_novo: string; situacao_anterior: string; situacao_nova: string; motivo: string; autor_nome: string; created_at: string }[] }> =>
    (await api.get(`/atendimentos/${id}/organizacao/`, { timeout: 15000 })).data,
  bibliotecaModelos: async (busca: string): Promise<{ modelos: ModeloBiblioteca[]; mais_resultados: boolean }> =>
    (await api.get('/atendimentos/biblioteca-modelos/', { params: { busca }, timeout: 15000 })).data,
  publicarModelo: async (id: string, modelo_id: string, nome: string): Promise<{ id: string; nome: string }> =>
    (await api.post(`/atendimentos/${id}/publicar-modelo/`, { modelo_id, nome, confirmar_sem_dados: true }, { timeout: 15000 })).data,
  compararMinutas: async (id: string, base: string, destino: string): Promise<ComparacaoMinutas> =>
    (await api.get(`/atendimentos/${id}/comparar-minutas/`, { params: { base, destino }, timeout: 15000 })).data,
  interpretarMensagem: async (id: string, mensagem_id: string): Promise<{ mensagem_id: string; propostas: { campo: string; valor: string; trecho: string }[]; duvidas: string[]; aviso: string }> =>
    (await api.post(`/atendimentos/${id}/interpretar-mensagem/`, { mensagem_id }, { timeout: 40000 })).data,
  editarMinuta: async (id: string, data: { minuta_id: string; versao_esperada: number; client_id: string; corpo: string; motivo: string }): Promise<{ id: string; versao: number }> => (await api.post(`/atendimentos/${id}/editar-minuta/`, data, { timeout: 15000 })).data,
  exportarMinuta: async (id: string, minuta: string, formato: 'pdf' | 'docx'): Promise<Blob> => (await api.get(`/atendimentos/${id}/minutas/${minuta}/exportar/`, { params: { formato }, responseType: 'blob', timeout: 30000 })).data,
  modelos: async (id: string): Promise<{ base: TextoModelo; modelo_ficticio_estruturado: TextoModelo; referencias_complementares: { nome: string; variante: string; aprovado: false; aviso: string; modelo: TextoModelo }[]; referencia: { nome: string; versao: string; aprovado: false; aviso: string; modelo: TextoModelo }; marcadores: { chave: string; rotulo: string }[]; versoes: ModeloMinuta[] }> => (await api.get(`/atendimentos/${id}/modelo-minuta/`, { timeout: 15000 })).data,
  salvarModelo: async (id: string, data: TextoModelo & { aprovado: boolean; justificativa: string; versao_esperada: number; referencia_id?: string | null }): Promise<ModeloMinuta> => (await api.post(`/atendimentos/${id}/modelo-minuta/`, data, { timeout: 15000 })).data,
  redacao: async (id: string): Promise<EstadoRedacao> => (await api.get(`/atendimentos/${id}/minuta-preparada/`, { timeout: 15000 })).data,
  prepararMinuta: async (id: string, assinatura_esperada: string): Promise<EstadoRedacao> => (await api.post(`/atendimentos/${id}/minuta-preparada/`, { assinatura_esperada }, { timeout: 15000 })).data,
  conferencia: async (id: string): Promise<Conferencia> => (await api.get(`/atendimentos/${id}/conferencia/`, { timeout: 15000 })).data,
  responder: async (id: string, data: RespostaConferencia): Promise<{ mensagem: Mensagem; conferencia: Conferencia }> => (await api.post(`/atendimentos/${id}/responder/`, data, { timeout: 15000 })).data,
  anexos: async (id: string): Promise<Anexo[]> => (await api.get(`/atendimentos/${id}/anexos/`, { timeout: 15000 })).data,
  upload: async (id: string, file: File): Promise<Anexo> => {
    const form = new FormData(); form.append('arquivo', file)
    return (await api.post(`/atendimentos/${id}/anexos/`, form, { timeout: 150000 })).data
  },
  imagemPagina: async (id: string, anexoId: string, paginaId: string): Promise<Blob> => (await api.get(`/atendimentos/${id}/anexos/${anexoId}/paginas/${paginaId}/imagem/`, { responseType: 'blob', timeout: 20000 })).data,
  relerAnexo: async (id: string, anexoId: string, leitura_versao: number): Promise<Anexo> => (await api.post(`/atendimentos/${id}/anexos/${anexoId}/reler/`, { leitura_versao }, { timeout: 150000 })).data,
  download: async (id: string, anexoId: string): Promise<Blob> => (await api.get(`/atendimentos/${id}/anexos/${anexoId}/download/`, { responseType: 'blob', timeout: 15000 })).data,
  ficha: async (id: string): Promise<{ campos: CampoFicha[] }> => (await api.get(`/atendimentos/${id}/ficha/`, { timeout: 15000 })).data,
  updateField: async (id: string, data: AtualizarDado): Promise<RevisaoDado> =>
    (await api.post(`/atendimentos/${id}/ficha/`, data, { timeout: 15000 })).data,
  list: async (params?: { busca: string; situacao: string }): Promise<Atendimento[]> => (await api.get('/atendimentos/', { params, timeout: 15000 })).data,
  create: async (titulo: string): Promise<Atendimento> => (await api.post('/atendimentos/', { titulo }, { timeout: 15000 })).data,
  get: async (id: string): Promise<Atendimento> => (await api.get(`/atendimentos/${id}/`, { timeout: 15000 })).data,
  messages: async (id: string): Promise<Mensagem[]> => (await api.get(`/atendimentos/${id}/mensagens/`, { timeout: 15000 })).data,
  send: async (id: string, texto: string, client_id: string): Promise<Mensagem> =>
    (await api.post(`/atendimentos/${id}/mensagens/`, { texto, client_id }, { timeout: 15000 })).data,
}
