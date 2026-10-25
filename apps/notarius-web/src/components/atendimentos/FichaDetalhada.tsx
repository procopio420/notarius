'use client'
import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type FonteDocumento, type Mensagem, type PedidoFicha } from '@/lib/atendimentos'
import { useRascunhoSessao } from '@/lib/rascunhoSessao'
import { fichaDetalhadaApi, type RegistroFicha, type CampoDetalhado, type RevisaoDetalhada, type TipoRegistro, type SituacaoDetalhada } from '@/lib/fichaDetalhada'
import { propostasDadosApi, situacoesProposta, type PropostaEvidencia } from '@/lib/propostasDados'

const tipos: Record<TipoRegistro, string> = { pessoa: 'Pessoas', papel: 'Papéis no negócio', relacao: 'Relações entre pessoas', imovel: 'Imóveis', negociacao: 'Preço e pagamento', ato: 'Dados do ato', complemento: 'Declarações, documentos e complementos' }
const situacoes: Record<SituacaoDetalhada, string> = { ausente: 'Ausente', extraido: 'Extraído, sem confirmação', informado: 'Informado pela escrevente', confirmado: 'Confirmado pela escrevente', divergente: 'Divergente', ilegivel: 'Leitura incerta' }
const opcoes: Record<string, string> = { conjuge_de: 'Cônjuge da segunda pessoa', representante_de: 'Representante da segunda pessoa', declarado_realizado: 'Declarado como realizado', comprovante_apresentado: 'Comprovante apresentado', a_esclarecer: 'A esclarecer', nao_realizado: 'Não realizado' }

function mensagemErro(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(mensagemErro).join(' ')
  if (value && typeof value === 'object') return Object.values(value).map(mensagemErro).join(' ')
  return 'Não foi possível salvar. Seu texto foi mantido.'
}

interface RascunhoFicha {
  modo: 'campo' | 'criacao'; objeto_id?: string; campo?: string; versao: number; contexto: string;
  modelo: string | null; tipo: TipoRegistro; escopo: string; a: string; b: string; imovel: string;
  valor: string; original: string; status: SituacaoDetalhada; fonte: string; trecho: string; canal: 'texto' | 'ocr';
  documento_versao: number; proposta_versao: number | null; motivo: string
}
function rascunhoValido(value: unknown): value is RascunhoFicha {
  const v = value as RascunhoFicha
  return !!v && ['campo', 'criacao'].includes(v.modo) && typeof v.valor === 'string' && typeof v.fonte === 'string' && typeof v.motivo === 'string' && typeof v.versao === 'number' && typeof v.contexto === 'string'
}
const rascunhosValidos = (value: unknown): value is RascunhoFicha[] => Array.isArray(value) && value.every(rascunhoValido)
const draftKey = (d: Pick<RascunhoFicha, 'modo' | 'objeto_id' | 'campo'>) => d.modo === 'criacao' ? 'criacao' : `${d.objeto_id}:${d.campo}`

export function FichaDetalhada({ id, scope, messages, selectedMessage, selectedDocument, onUsed, onLegacy, pedido, onPedidoConsumido }: {
  pedido?: PedidoFicha | null; onPedidoConsumido?: () => void
  id: string; scope: (string | undefined)[]; messages: Mensagem[]; selectedMessage: Mensagem | null; selectedDocument: FonteDocumento | null; onUsed: () => void; onLegacy: () => void
}) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const [tipo, setTipo] = useState<TipoRegistro>('pessoa')
  const [escopo, setEscopo] = useState('')
  const [creating, setCreating] = useState(false)
  const [a, setA] = useState(''); const [b, setB] = useState(''); const [imovel, setImovel] = useState('')
  const [reason, setReason] = useState('')
  const [expectedDocument, setExpectedDocument] = useState(0)
  const [expectedModel, setExpectedModel] = useState<string | null>(null)
  const [expectedFieldVersion, setExpectedFieldVersion] = useState(0)
  const formDraft = useRascunhoSessao<RascunhoFicha[]>(scope, 'ficha', [], rascunhosValidos)
  const attemptDraft = useRascunhoSessao(scope, 'envio-ficha', { signature: '', id: '' }, (v): v is { signature: string; id: string } => !!v && typeof (v as { signature?: unknown }).signature === 'string' && typeof (v as { id?: unknown }).id === 'string')
  const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const [editing, setEditing] = useState<{ obj: RegistroFicha; field: CampoDetalhado } | null>(null)
  const [value, setValue] = useState(''); const [original, setOriginal] = useState('')
  const [status, setStatus] = useState<SituacaoDetalhada>('informado')
  const [source, setSource] = useState('manual'); const [excerpt, setExcerpt] = useState('')
  const [channel, setChannel] = useState<'texto' | 'ocr'>('texto')
  const [confirm, setConfirm] = useState(false); const [checkedSource, setCheckedSource] = useState(false)
  const [history, setHistory] = useState<CampoDetalhado | null>(null)
  const [selectedProposal, setSelectedProposal] = useState<string | null>(null)
  const [checkedAssociation, setCheckedAssociation] = useState(false)
  const [expectedProposalVersion, setExpectedProposalVersion] = useState<number | null>(null)
  const [rejecting, setRejecting] = useState<PropostaEvidencia | null>(null)
  const [sourceView, setSourceView] = useState<PropostaEvidencia | null>(null)
  const proposalRetry = useRef<{ signature: string; id: string } | null>(null)
  const retry = useRef<{ signature: string; id: string } | null>(null)
  const data = useQuery({ queryKey: ['ficha-detalhada', ...scope], queryFn: () => fichaDetalhadaApi.get(id), enabled: open })
  const files = useQuery({ queryKey: ['anexos-atendimento', ...scope], queryFn: () => atendimentosApi.anexos(id), enabled: open })
  const proposalSource = useQuery({ queryKey: ['fonte-proposta', ...scope, sourceView?.id], queryFn: () => propostasDadosApi.fonte(id, sourceView!.id), enabled: !!sourceView })
  useEffect(() => { if (selectedMessage || selectedDocument) setOpen(true) }, [selectedMessage, selectedDocument])
  const objetos = data.data?.objetos || []
  const pessoas = objetos.filter(o => o.tipo === 'pessoa')
  const pages = (files.data || []).flatMap(file => file.paginas.map(page => ({ file, page })))
  const proposals = data.data?.propostas || []
  const currentProposal = proposals.find(p => source === `proposta:${p.id}`)
  const currentPage = pages.find(p => source === `pagina:${p.page.id}` || currentProposal?.origem.pagina_id === p.page.id)
  const currentMessage = messages.find(m => source === `mensagem:${m.id}` || currentProposal?.origem.mensagem_id === m.id)
  const currentLegacy = data.data?.legado.find(r => source === `legado:${r.id}`)
  const sourceText = (currentPage ? (channel === 'ocr' ? currentPage.page.texto_ocr : currentPage.page.texto) : currentMessage?.texto ?? currentLegacy?.valor) ?? currentProposal?.trecho

  function titulo(obj: RegistroFicha): string {
    if (obj.rotulo) return obj.rotulo
    const key = obj.tipo === 'pessoa' ? 'nome' : obj.tipo === 'papel' ? 'tipo_papel' : obj.tipo === 'relacao' ? 'tipo_relacao' : obj.tipo === 'negociacao' ? 'preco' : obj.tipo === 'complemento' ? 'assunto' : obj.tipo === 'ato' ? 'referencia' : 'descricao'
    const label = obj.campos.find(f => f.chave === key)?.atual?.valor || tipos[obj.tipo]
    return `${opcoes[label] || label.slice(0, 90)} · ${obj.id.slice(0, 8)}`
  }
  function resetConfirmation() { setConfirm(false); setCheckedSource(false); setCheckedAssociation(false) }
  function edit(obj: RegistroFicha, field: CampoDetalhado, requestedProposal?: string | null) {
    const saved = formDraft.value.find(d => d.modo === 'campo' && d.objeto_id === obj.id && d.campo === field.chave)
    if (saved && !editing) { void resumeDraft(saved); return }
    const doc = requestedProposal !== undefined ? null : selectedDocument
    const msg = requestedProposal !== undefined ? null : selectedMessage
    const activeProposal = requestedProposal !== undefined ? requestedProposal : selectedProposal
    setExpectedFieldVersion(field.atual?.versao || 0)
    setExpectedProposalVersion(null)
    setExpectedModel(data.data?.modelo_id ?? null)
    setEditing({ obj, field }); setError(''); setReason(''); resetConfirmation()
    const old = field.atual
    setValue(doc?.trecho || msg?.texto || old?.valor || '')
    setOriginal(doc?.trecho || msg?.texto || old?.valor_original || old?.valor || '')
    const origin = old?.origem
    const pageId = doc?.pagina_id || origin?.pagina_id
    setExpectedDocument(doc?.organizacao_versao ?? pages.find(p => p.page.id === pageId)?.file.organizacao.versao ?? 0)
    setSource(doc ? `pagina:${doc.pagina_id}` : msg ? `mensagem:${msg.id}` : origin?.tipo === 'documento' ? `pagina:${origin.pagina_id}` : origin?.tipo === 'mensagem' ? `mensagem:${origin.mensagem_id}` : origin?.tipo === 'legado' ? `legado:${origin.revisao_id}` : 'manual')
    setExcerpt(doc?.trecho || msg?.texto || origin?.trecho || '')
    setChannel(doc?.canal || origin?.canal || 'texto'); setStatus('informado')
    const proposal = proposals.find(p => p.id === activeProposal || (!activeProposal && old?.propostas_ids?.includes(p.id)))
    if (proposal) {
      setExpectedProposalVersion(proposal.versao_decisao)
      setExpectedDocument(pages.find(p => p.page.id === proposal.origem.pagina_id)?.file.organizacao.versao ?? 0)
      setSource(`proposta:${proposal.id}`); setExcerpt(proposal.trecho); setOriginal(proposal.valor_original); setChannel(proposal.origem.canal)
      const nextValue = activeProposal ? proposal.valor_original : old?.valor || proposal.valor_original
      setValue(field.opcoes && !field.opcoes.includes(nextValue) ? '' : nextValue)
    }
  }
  const editRef = useRef(edit); editRef.current = edit
  const savedDraftsRef = useRef(formDraft.value); savedDraftsRef.current = formDraft.value
  const resumeRef = useRef(resumeDraft); resumeRef.current = resumeDraft
  const handledRequest = useRef('')
  useEffect(() => {
    if (!pedido || pedido.token === handledRequest.current) return
    setOpen(true)
    if (!data.data) return
    handledRequest.current = pedido.token
    setError(''); setSelectedProposal(pedido.proposta_id || null)
    if (pedido.novo_participante) {
      const saved = savedDraftsRef.current.find(d => d.modo === 'criacao')
      if (saved) { void resumeRef.current(saved); onPedidoConsumido?.(); return }
      setEditing(null); setTipo('pessoa'); setEscopo(''); setA(''); setB(''); setImovel('');
      setExpectedModel(data.data.modelo_id); setReason(''); setCreating(true)
    } else if (pedido.objeto_id && pedido.campo) {
      const obj = data.data.objetos.find(o => o.id === pedido.objeto_id)
      const field = obj?.campos.find(f => f.chave === pedido.campo)
      if (obj && field) { setTipo(obj.tipo); editRef.current(obj, field, pedido.proposta_id || null) }
      else setError('O registro ou campo não está mais disponível. Confira a pendência atual sem reaproveitar uma associação antiga.')
    }
    onPedidoConsumido?.()
  }, [pedido, data.data, onPedidoConsumido])

  const draftReady = formDraft.ready, saveLocalDraft = formDraft.save
  useEffect(() => {
    if (!draftReady || (!editing && !creating)) return
    const snapshot: RascunhoFicha = { modo: creating ? 'criacao' : 'campo', objeto_id: editing?.obj.id, campo: editing?.field.chave,
      versao: expectedFieldVersion, contexto: editing?.field.contexto_assinatura || '', modelo: expectedModel,
      tipo, escopo, a, b, imovel, valor: value, original, status, fonte: source, trecho: excerpt, canal: channel,
      documento_versao: expectedDocument, proposta_versao: expectedProposalVersion, motivo: reason }
    saveLocalDraft(old => [...old.filter(d => draftKey(d) !== draftKey(snapshot)), snapshot])
  }, [draftReady, saveLocalDraft, editing, creating, expectedFieldVersion, expectedModel, tipo, escopo, a, b, imovel, value, original, status, source, excerpt, channel, expectedDocument, expectedProposalVersion, reason])

  async function resumeDraft(saved: RascunhoFicha) {
    if (!saved || busy) return
    setOpen(true); setError('')
    const fresh = (await data.refetch()).data
    if (!fresh) { setError('Não foi possível atualizar a ficha. O rascunho local foi mantido.'); return }
    if (saved.modo === 'campo') {
      const obj = fresh.objetos.find(o => o.id === saved.objeto_id)
      const field = obj?.campos.find(f => f.chave === saved.campo)
      if (!obj || !field) { setError('O campo do rascunho não está disponível no modelo atual. Revise manualmente; o texto local foi preservado.'); return }
      setEditing({ obj, field: { ...field, contexto_assinatura: saved.contexto } }); setCreating(false)
    } else { setEditing(null); setCreating(true) }
    setExpectedFieldVersion(saved.versao); setExpectedModel(saved.modelo); setTipo(saved.tipo); setEscopo(saved.escopo)
    setA(saved.a); setB(saved.b); setImovel(saved.imovel); setValue(saved.valor); setOriginal(saved.original)
    setStatus(saved.status); setSource(saved.fonte); setExcerpt(saved.trecho); setChannel(saved.canal)
    setExpectedDocument(saved.documento_versao); setExpectedProposalVersion(saved.proposta_versao); setReason(saved.motivo)
    resetConfirmation()
  }
  function chooseSource(next: string) {
    const page = pages.find(p => next === `pagina:${p.page.id}` || (next.startsWith('proposta:') && proposals.find(q => next === `proposta:${q.id}`)?.origem.pagina_id === p.page.id))
    setExpectedDocument(page?.file.organizacao.versao ?? 0)
    setSource(next); setExcerpt(''); setOriginal(''); setExpectedProposalVersion(null); resetConfirmation()
    const proposal = proposals.find(p => next === `proposta:${p.id}`)
    if (proposal) {
      setExpectedProposalVersion(proposal.versao_decisao)
      setExcerpt(proposal.trecho); setOriginal(proposal.valor_original); setChannel(proposal.origem.canal)
      setValue(editing?.field.opcoes && !editing.field.opcoes.includes(proposal.valor_original) ? '' : proposal.valor_original)
    }
  }
  async function send(payload: object) {
    const signature = JSON.stringify(payload)
    if (retry.current?.signature !== signature) retry.current = { signature, id: attemptDraft.value.signature === signature && attemptDraft.value.id ? attemptDraft.value.id : crypto.randomUUID() }
    attemptDraft.save(retry.current)
    setBusy(true); setError('')
    try {
      await fichaDetalhadaApi.alterar(id, { ...payload, client_id: retry.current.id })
      await Promise.all(['ficha-detalhada', 'ficha-atendimento', 'mensagens-atendimento', 'conferencia-atendimento', 'minuta-atendimento', 'atendimentos'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      retry.current = null
      attemptDraft.clear()
      formDraft.save(old => old.filter(d => creating ? d.modo !== 'criacao' : d.objeto_id !== editing?.obj.id || d.campo !== editing?.field.chave))
      setCreating(false); setEditing(null); setReason(''); setSelectedProposal(null); onUsed()
    } catch (err) {
      const response = (err as { response?: { status?: number; data?: unknown } }).response
      setError(response?.status === 409 ? 'O registro, a fonte ou o modelo mudou. Feche este campo, atualize e confira antes de tentar novamente.' : mensagemErro(response?.data))
      if (response?.status === 409) void data.refetch()
    } finally { setBusy(false) }
  }
  function create() {
    void send({ operacao: 'criar', tipo, modelo_id: expectedModel, justificativa: reason,
      ...(tipo === 'complemento' ? { escopo, ...(['pessoa', 'pessoa_imovel'].includes(escopo) ? { pessoa_a_id: a } : {}), ...(['imovel', 'pessoa_imovel'].includes(escopo) ? { imovel_id: imovel } : {}) } : {}),
      ...(tipo === 'papel' || tipo === 'relacao' ? { pessoa_a_id: a } : {}), ...(tipo === 'relacao' ? { pessoa_b_id: b } : {}), ...(tipo === 'negociacao' ? { imovel_id: imovel } : {}) })
  }
  function save() {
    if (!editing) return
    const [kind, sourceId] = currentProposal ? [currentProposal.origem.tipo === 'documento' ? 'pagina' : 'mensagem', currentProposal.origem.pagina_id || currentProposal.origem.mensagem_id] : source.split(':')
    const origin = kind === 'pagina' ? 'documento' : kind
    void send({ operacao: 'salvar', objeto_id: editing.obj.id, modelo_id: expectedModel, justificativa: reason,
      campos: [{ chave: editing.field.chave, valor: status === 'ausente' ? '' : value, valor_original: source === 'manual' ? (status === 'ausente' ? '' : value) : original,
        contexto_assinatura: editing.field.contexto_assinatura, organizacao_versao: expectedDocument,
        situacao: status, versao_esperada: expectedFieldVersion, confirmar: confirm, conferir_fonte: checkedSource,
        ...(currentProposal ? { proposta_id: currentProposal.id, versao_proposta: expectedProposalVersion, conferir_associacao: checkedAssociation } : {}),
        origem: origin, ...(kind === 'pagina' ? { pagina_id: sourceId, leitura_versao: currentProposal?.origem.leitura_versao ?? currentPage?.file.leitura_versao } : {}),
        ...(kind === 'mensagem' ? { mensagem_id: sourceId } : {}), ...(kind === 'legado' ? { revisao_origem_id: sourceId } : {}),
        trecho_origem: excerpt, canal_origem: channel }] })
  }
  async function rejectProposal() {
    if (!rejecting || busy) return
    const payload = { proposta_id: rejecting.id, versao_esperada: rejecting.versao_decisao, justificativa: reason }
    const signature = JSON.stringify(payload)
    if (proposalRetry.current?.signature !== signature) proposalRetry.current = { signature, id: crypto.randomUUID() }
    setBusy(true); setError('')
    try {
      await propostasDadosApi.rejeitar(id, { ...payload, client_id: proposalRetry.current.id })
      await Promise.all(['ficha-detalhada', 'propostas-dados', 'conferencia-atendimento', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      proposalRetry.current = null; setRejecting(null); setReason('')
    } catch (err) { setError(mensagemErro((err as { response?: { data?: unknown } }).response?.data)) }
    finally { setBusy(false) }
  }
  function showRevision(r: RevisaoDetalhada) {
    return <Box key={r.id} sx={{ borderBottom: '1px solid #ddd', pb: 2 }}>
      <Typography fontWeight={600}>v{r.versao} · {situacoes[r.situacao]}</Typography>
      <Typography sx={{ whiteSpace: 'pre-wrap' }}>Original: {r.valor_original || '(sem valor)'}</Typography>
      <Typography sx={{ whiteSpace: 'pre-wrap' }}>Revisado: {r.valor || '(sem valor)'}</Typography>
      <Typography variant="body2">Fonte: {r.origem.tipo} · {r.origem.arquivo || r.origem.mensagem_id || r.origem.revisao_id}{r.origem.pagina ? ` · página ${r.origem.pagina} · leitura ${r.origem.leitura_versao}` : ''}</Typography>
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Trecho: {r.origem.trecho}</Typography>
      {!!r.propostas_ids?.length && <Typography variant="caption">Esta revisão está ligada às propostas e às decisões preservadas em “Propostas com fonte”.</Typography>}
      {r.propostas_ids?.map(proposalId => {
        const proposal = proposals.find(p => p.id === proposalId)
        return proposal ? <Button key={proposalId} onClick={() => { setHistory(null); setSourceView(proposal) }}>Abrir fonte da proposta vinculada</Button> : null
      })}
      {!r.fonte_atual && <Alert severity="warning">Esta leitura foi substituída. É necessária nova revisão da fonte atual.</Alert>}
      <Typography variant="body2">{r.autor_nome || 'Escrevente'} · {new Date(r.created_at).toLocaleString('pt-BR')} · {r.justificativa}</Typography>
      {r.validacao_formato && <Alert severity="info">Formato: {r.validacao_formato.formato_consistente ? 'consistente' : 'não consistente'}. Dígitos: {r.validacao_formato.digitos_consistentes ? 'consistentes' : 'não consistentes'}. {r.validacao_formato.aviso}</Alert>}
    </Box>
  }
  return <>
    <Button id="abrir-ficha-detalhada" variant="contained" onClick={() => { setOpen(true); setError('') }}>Ficha detalhada: pessoas e negócio</Button>
    {formDraft.value.map(d => <Button key={draftKey(d)} onClick={() => resumeDraft(d)}>Retomar rascunho {d.modo === 'criacao' ? 'de novo registro' : `${d.campo} · ${d.objeto_id?.slice(0, 8)}`}, sem confirmar</Button>)}
    {formDraft.aviso && <Alert severity="warning">{formDraft.aviso}</Alert>}
    {attemptDraft.aviso && <Alert severity="warning">{attemptDraft.aviso}</Alert>}
    <Dialog open={open} onClose={() => { if (!busy) { setOpen(false); onUsed() } }} fullWidth maxWidth="md">
      <DialogTitle>Ficha de compra e venda</DialogTitle><DialogContent><Stack spacing={2}>
        {error && !editing && !creating && <Alert severity="error">{error}</Alert>}
        <Alert severity="info">Pessoas, papéis e relações são registros separados. Nenhuma relação é deduzida por nome ou estado civil. Dados de formato consistente não comprovam identidade.</Alert>
        {(selectedMessage || selectedDocument) && <Alert severity="info">Fonte selecionada. Escolha explicitamente o registro e o campo para revisar o trecho. <Button onClick={() => { setOpen(false); onLegacy() }}>Usar nos blocos antigos</Button></Alert>}
        {data.isLoading && <Typography>Carregando ficha…</Typography>}
        {data.isError && <Alert severity="error" action={<Button onClick={() => data.refetch()}>Tentar novamente</Button>}>Não foi possível consultar os dados.</Alert>}
        {selectedProposal && <Alert severity="info">Proposta selecionada. Escolha explicitamente o registro e abra o campo correspondente abaixo; nenhuma pessoa foi escolhida pelo sistema. <Button onClick={() => setSelectedProposal(null)}>Cancelar seleção</Button></Alert>}
        {!!proposals.length && <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer', py: 1 }}>Propostas com fonte ({proposals.length})</Typography>
          <Alert severity="warning">Propostas para revisão humana. Rótulos locais e respostas simuladas de testes não são IA real funcionando. Trecho literal não garante interpretação correta ou associação à pessoa certa.</Alert>
          {proposals.map(p => <Box key={p.id} sx={{ borderBottom: '1px solid #ddd', py: 2 }}>
            <Typography fontWeight={600}>{p.rotulo} · {situacoesProposta[p.situacao] || p.situacao}</Typography>
            <Typography sx={{ whiteSpace: 'pre-wrap' }}>Original: {p.valor_original}</Typography>
            {p.analise_documental_id && <Alert severity="info">Análise estruturada simulada em teste. Destino {p.evidencia_estruturada?.registro_sugerido_id ? `apenas sugerido: ${p.evidencia_estruturada.registro_sugerido_id}` : 'incerto, sem vínculo'}. Escolha e confira o registro explicitamente.</Alert>}
            {p.evidencia_estruturada?.contexto && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Contexto completo da unidade: {p.evidencia_estruturada.contexto}</Typography>}
            <Typography variant="body2">Fonte: {p.origem.arquivo || 'mensagem da conversa'}{p.origem.pagina ? ` · página ${p.origem.pagina} · leitura ${p.origem.leitura_versao}` : ''} · {p.origem.canal} · linha {p.origem.linha}</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Trecho: {p.trecho}</Typography>
            {p.origem.leitura_situacao === 'revisao' && <Alert severity="warning">Leitura incerta: {p.origem.leitura_aviso} Confira o original antes de decidir.</Alert>}
            {!p.fonte_atual && <Alert severity="warning">A fonte, a leitura ou a classificação mudou. A proposta histórica foi preservada; confira a fonte atual antes de aceitar dados.</Alert>}
            <Typography variant="caption">Campos propostos: {p.destinos.map(d => d.rotulo).join(', ')}. A associação ao registro é decisão da escrevente.</Typography>
            <Stack direction="row" flexWrap="wrap"><Button onClick={() => setSourceView(p)}>Abrir fonte e contexto</Button><Button disabled={busy || !p.fonte_atual} onClick={() => setSelectedProposal(p.id)}>Selecionar para conferir na ficha</Button>
              <Button disabled={busy} onClick={() => { setRejecting(p); setReason(''); setError('') }}>Não usar esta proposta</Button></Stack>
            <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Decisões e histórico ({p.decisoes.length})</Typography>{p.decisoes.map(d => <Box key={d.id} sx={{ p: 1 }}><Typography>v{d.versao} · {d.acao} · {d.autor_nome} · {new Date(d.data).toLocaleString('pt-BR')}</Typography><Typography>{d.justificativa}</Typography><Typography variant="caption">Registro: {d.objeto_id || 'nenhum'} · revisão: {d.revisao_id || 'nenhuma'}</Typography></Box>)}</Box>
          </Box>)}
        </Box>}
        <TextField disabled={busy} select label="Grupo de registros" value={tipo} onChange={e => setTipo(e.target.value as TipoRegistro)}>{Object.entries(tipos).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}</TextField>
        <Button disabled={!data.data || busy} onClick={() => { const saved = formDraft.value.find(d => d.modo === 'criacao'); if (saved) { void resumeDraft(saved); return } setCreating(true); setEscopo(''); setExpectedModel(data.data?.modelo_id ?? null); setA(''); setB(''); setImovel(''); setReason(''); setError('') }}>{formDraft.value.some(d => d.modo === 'criacao') ? 'Retomar novo registro pendente' : `Adicionar registro em ${tipos[tipo]}`}</Button>
        {objetos.filter(o => o.tipo === tipo).map(obj => <Box key={obj.id} sx={{ border: '1px solid #dce4ee', borderRadius: 2, p: 2 }}>
          <Typography fontWeight={600}>{titulo(obj)}</Typography>
          <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>Identificador: {obj.id}</Typography>
          {obj.criacao && <Typography variant="caption" display="block">Registro criado por {obj.criacao.autor_nome} · {new Date(obj.criacao.data).toLocaleString('pt-BR')}. {obj.criacao.motivo || 'Motivo de criação não registrado nesta versão antiga.'}</Typography>}
          {obj.pessoa_a_id && <Typography>Primeira pessoa: {pessoas.find(p => p.id === obj.pessoa_a_id) ? titulo(pessoas.find(p => p.id === obj.pessoa_a_id)!) : obj.pessoa_a_id}</Typography>}
          {obj.pessoa_b_id && <Typography>Segunda pessoa: {pessoas.find(p => p.id === obj.pessoa_b_id) ? titulo(pessoas.find(p => p.id === obj.pessoa_b_id)!) : obj.pessoa_b_id}</Typography>}
          {obj.imovel_id && <Typography>Imóvel: {objetos.find(o => o.id === obj.imovel_id) ? titulo(objetos.find(o => o.id === obj.imovel_id)!) : obj.imovel_id}</Typography>}
          {[...new Set(obj.campos.map(f => f.grupo))].map(group => <Box component="details" key={group} sx={{ mt: 1 }}><Typography component="summary" sx={{ cursor: 'pointer', py: 1 }}>{group}</Typography>
            <Stack spacing={1}>{obj.campos.filter(f => f.grupo === group).map(field => <Box key={field.chave}>
              <Typography component="div">{field.rotulo} <Chip size="small" label={field.atual?.situacao_efetiva === 'reaberta' ? 'Precisa de nova revisão' : situacoes[field.atual?.situacao || 'ausente']} /></Typography>
              <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{field.atual?.valor || 'Sem informação registrada'}</Typography>
              {field.atual && !field.atual.fonte_atual && <Alert severity="warning">Fonte desatualizada; precisa de revisão.</Alert>}
              {field.atual && !field.atual.dependencias_atuais && <Alert severity="warning">Classificação, situação ou registro vinculado mudou; confira novamente este dado.</Alert>}
              <Button onClick={() => edit(obj, field)}>Conferir campo</Button><Button disabled={!field.historico.length} onClick={() => setHistory(field)}>Origem e histórico</Button>
            </Box>)}</Stack>
          </Box>)}
        </Box>)}
        {data.data?.legado.length ? <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Conteúdo antigo para revisão ({data.data.legado.length} versões)</Typography>
          <Alert severity="warning">Textos preservados integralmente. As confirmações antigas não confirmam automaticamente os novos registros. Nenhuma pessoa foi repartida ou associada pelo sistema.</Alert>
          {data.data.legado.map(r => <Box key={r.id}><Typography fontWeight={600}>{r.chave} · versão {r.versao}</Typography>{showRevision(r)}</Box>)}
        </Box> : null}
        {objetos.length > 0 && <Alert severity="warning">O preenchimento usa as posições e os campos do modelo aprovado. Resolva as pendências e confira a vinculação na aba Minuta; os blocos antigos não são atualizados automaticamente.</Alert>}
      </Stack></DialogContent><DialogActions><Button onClick={() => { setOpen(false); onUsed() }}>Fechar ficha</Button></DialogActions>
    </Dialog>
    <Dialog open={creating} onClose={() => !busy && setCreating(false)} fullWidth maxWidth="sm"><DialogTitle>Novo registro · {tipos[tipo]}</DialogTitle><DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      {tipo === 'complemento' && <><Alert severity="info">Crie um complemento por documento, consulta, declaração ou assunto. Escolha a quem ele se refere; não misture pessoas ou imóveis no mesmo registro.</Alert><TextField select label="A quem este complemento se refere?" value={escopo} disabled={busy} onChange={e => { setEscopo(e.target.value); setA(''); setImovel('') }}><MenuItem value="atendimento">Ao atendimento, sem pessoa ou imóvel específico</MenuItem><MenuItem value="pessoa">A uma pessoa</MenuItem><MenuItem value="imovel">A um imóvel</MenuItem><MenuItem value="pessoa_imovel">A uma pessoa e um imóvel</MenuItem></TextField></>}
      {(tipo === 'papel' || tipo === 'relacao' || tipo === 'complemento' && ['pessoa', 'pessoa_imovel'].includes(escopo)) && <TextField disabled={busy} select label={tipo === 'complemento' ? 'Pessoa a que o complemento se refere' : tipo === 'papel' ? 'Pessoa que terá o papel' : 'Primeira pessoa (representante ou cônjuge)'} value={a} onChange={e => setA(e.target.value)}>{pessoas.map(p => <MenuItem key={p.id} value={p.id}>{titulo(p)}</MenuItem>)}</TextField>}
      {tipo === 'relacao' && <TextField disabled={busy} select label="Segunda pessoa (representada ou cônjuge)" value={b} onChange={e => setB(e.target.value)}>{pessoas.filter(p => p.id !== a).map(p => <MenuItem key={p.id} value={p.id}>{titulo(p)}</MenuItem>)}</TextField>}
      {(tipo === 'negociacao' || tipo === 'complemento' && ['imovel', 'pessoa_imovel'].includes(escopo)) && <TextField disabled={busy} select label={tipo === 'complemento' ? 'Imóvel a que o complemento se refere' : 'Imóvel desta negociação'} value={imovel} onChange={e => setImovel(e.target.value)}>{objetos.filter(o => o.tipo === 'imovel').map(p => <MenuItem key={p.id} value={p.id}>{titulo(p)}</MenuItem>)}</TextField>}
      <Typography>O identificador é criado agora. Os dados serão informados e confirmados em campos separados.</Typography>
      <TextField disabled={busy} label="Motivo do registro" value={reason} onChange={e => setReason(e.target.value)} required />
      {error && <Alert severity="error">{error}</Alert>}
    </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => { setCreating(false); formDraft.save(old => old.filter(d => d.modo !== 'criacao')) }}>Descartar só este rascunho local</Button><Button disabled={busy} onClick={() => setCreating(false)}>Guardar rascunho e voltar</Button><Button disabled={busy || !reason.trim() || ((tipo === 'papel' || tipo === 'relacao') && !a) || (tipo === 'relacao' && !b) || (tipo === 'negociacao' && !imovel) || (tipo === 'complemento' && (!escopo || ['pessoa', 'pessoa_imovel'].includes(escopo) && !a || ['imovel', 'pessoa_imovel'].includes(escopo) && !imovel))} onClick={create}>Criar registro</Button></DialogActions></Dialog>
    <Dialog open={!!editing} onClose={() => !busy && setEditing(null)} fullWidth maxWidth="sm"><DialogTitle>{editing?.field.rotulo} · {editing ? titulo(editing.obj) : ''}</DialogTitle><DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      <TextField disabled={busy} select label="Fonte deste dado" value={source} onChange={e => chooseSource(e.target.value)}>
        <MenuItem value="manual">Informação expressa da escrevente (gera mensagem de origem)</MenuItem>
        {messages.map(m => <MenuItem key={m.id} value={`mensagem:${m.id}`} disabled={messages.some(n => n.correcao_de === m.id)}>Mensagem{messages.some(n => n.correcao_de === m.id) ? ' corrigida' : ''}: {m.texto.slice(0, 55)}</MenuItem>)}
        {pages.map(p => <MenuItem key={p.page.id} value={`pagina:${p.page.id}`}>{p.file.nome} · página {p.page.numero} · leitura {p.file.leitura_versao}</MenuItem>)}
        {data.data?.legado.map(r => <MenuItem key={r.id} value={`legado:${r.id}`}>Conteúdo antigo: {r.chave} · v{r.versao}</MenuItem>)}
        {proposals.map(p => <MenuItem key={p.id} value={`proposta:${p.id}`} disabled={!p.fonte_atual}>Proposta: {p.rotulo} · {p.origem.arquivo || 'mensagem'} · {p.id.slice(0, 8)}</MenuItem>)}
      </TextField>
      {currentPage && <TextField disabled={busy || !!currentProposal} select label="Leitura" value={channel} onChange={e => { setChannel(e.target.value as 'texto' | 'ocr'); resetConfirmation() }}><MenuItem value="texto">Texto da página</MenuItem><MenuItem value="ocr">OCR local</MenuItem></TextField>}
      {source !== 'manual' && <><Typography sx={{ whiteSpace: 'pre-wrap', maxHeight: 180, overflow: 'auto', bgcolor: 'action.hover', p: 2 }}>{sourceText || 'Fonte ou leitura indisponível. Atualize a ficha.'}</Typography>
        <TextField disabled={busy || !!currentProposal} label="Trecho literal da fonte" value={excerpt} multiline minRows={2} onChange={e => { setExcerpt(e.target.value); resetConfirmation() }} />
        <TextField disabled={busy || !!currentProposal} label="Valor original transcrito" value={original} multiline onChange={e => { setOriginal(e.target.value); resetConfirmation() }} />
      </>}
      <TextField disabled={busy} label="Valor revisado" value={value} multiline={!editing?.field.opcoes} select={!!editing?.field.opcoes} onChange={e => { setValue(e.target.value); resetConfirmation() }}>
        {editing?.field.opcoes?.map(o => <MenuItem key={o} value={o}>{opcoes[o] || o}</MenuItem>)}
      </TextField>
      <TextField disabled={busy} select label="Situação" value={status} onChange={e => { setStatus(e.target.value as SituacaoDetalhada); resetConfirmation() }}>{Object.entries(situacoes).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}</TextField>
      <TextField disabled={busy} label="Motivo da informação ou correção" value={reason} multiline onChange={e => setReason(e.target.value)} required />
      {currentProposal && <FormControlLabel control={<Checkbox disabled={busy} checked={checkedAssociation} onChange={e => setCheckedAssociation(e.target.checked)} />} label="Conferi que esta proposta pertence exatamente ao registro e ao campo escolhidos, considerando pessoas, papéis e contexto." />}
      {currentProposal && !currentProposal.fonte_atual && <Alert severity="warning">Esta proposta usa uma leitura substituída. Escolha uma fonte atual para registrar nova revisão.</Alert>}
      {status === 'confirmado' && <><FormControlLabel control={<Checkbox disabled={busy} checked={checkedSource} onChange={e => setCheckedSource(e.target.checked)} />} label="Conferi a fonte e a associação a este registro." />
        <FormControlLabel control={<Checkbox disabled={busy} checked={confirm} onChange={e => setConfirm(e.target.checked)} />} label="Confirmo este dado como escrevente. Não é comprovação automática de autenticidade." /></>}
      {editing?.field.chave === 'cpf' && <Alert severity="info">Formato e dígitos de CPF não comprovam identidade. O valor original é preservado.</Alert>}
      {editing?.obj.tipo === 'negociacao' && <Alert severity="info">Condição combinada, pagamento declarado, comprovante e quitação são dados diferentes. Não confirme acontecimento com base no modelo.</Alert>}
      {error && <Alert severity="error">{error}</Alert>}
      <Typography variant="caption">Rascunho somente nesta aba do navegador. Ao retomar, confirme fonte e dado novamente; as versões originais são mantidas e alterações concorrentes serão recusadas.</Typography>
    </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => { formDraft.save(old => old.filter(d => d.objeto_id !== editing?.obj.id || d.campo !== editing?.field.chave)); setEditing(null) }}>Descartar só este rascunho local</Button><Button disabled={busy} onClick={() => setEditing(null)}>Guardar rascunho e voltar</Button><Button disabled={busy || !reason.trim() || (!!currentProposal && (!checkedAssociation || !currentProposal.fonte_atual)) || (status === 'confirmado' && (!confirm || !checkedSource))} onClick={save}>Salvar nova versão</Button></DialogActions></Dialog>
    <Dialog open={!!rejecting} onClose={() => !busy && setRejecting(null)} fullWidth maxWidth="sm"><DialogTitle>Não usar esta proposta</DialogTitle><DialogContent><Stack spacing={2} sx={{ pt: 1 }}><Typography sx={{ whiteSpace: 'pre-wrap' }}>{rejecting?.trecho}</Typography><Typography>Informe o motivo. A proposta e as decisões anteriores permanecem no histórico. Se ela ainda sustenta um dado atual, revise esse dado primeiro.</Typography><TextField disabled={busy} label="Motivo da rejeição" multiline value={reason} onChange={e => setReason(e.target.value)} />{error && <Alert severity="error">{error}</Alert>}</Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setRejecting(null)}>Manter pendente</Button><Button disabled={busy || !reason.trim()} onClick={rejectProposal}>Registrar decisão</Button></DialogActions></Dialog>
    <Dialog open={!!history} onClose={() => setHistory(null)} fullWidth maxWidth="sm"><DialogTitle>Origem e histórico · {history?.rotulo}</DialogTitle><DialogContent><Stack spacing={2}>{history?.historico.map(showRevision)}</Stack></DialogContent><DialogActions><Button onClick={() => setHistory(null)}>Fechar</Button></DialogActions></Dialog>
    <Dialog open={!!sourceView} onClose={() => setSourceView(null)} fullWidth maxWidth="md"><DialogTitle>Fonte e contexto da proposta</DialogTitle><DialogContent><Stack spacing={2}>
      <Typography>{sourceView?.origem.arquivo || `Mensagem de origem: ${sourceView?.origem.mensagem_id || ''}`}{sourceView?.origem.pagina ? ` · página ${sourceView.origem.pagina} · leitura ${sourceView.origem.leitura_versao}` : ''}</Typography>
      <Alert severity="warning">Leia o contexto, não apenas o trecho. Esta exibição não comprova interpretação, identidade ou autenticidade.</Alert>
      {proposalSource.isLoading && <Typography>Consultando fonte preservada…</Typography>}
      {proposalSource.isError && <Alert severity="error">Não foi possível abrir o contexto. A revisão continua pendente; confira o original antes de decidir.</Alert>}
      {proposalSource.data && <><Typography sx={{ whiteSpace: 'pre-wrap', bgcolor: 'action.hover', p: 2 }}>{proposalSource.data.texto}</Typography><Typography sx={{ whiteSpace: 'pre-wrap' }}>Trecho da proposta: {proposalSource.data.trecho}</Typography>{!proposalSource.data.fonte_atual && <Alert severity="warning">Leitura histórica substituída. Confira a leitura atual.</Alert>}</>}
    </Stack></DialogContent><DialogActions><Button onClick={() => setSourceView(null)}>Voltar à revisão</Button></DialogActions></Dialog>
  </>
}
