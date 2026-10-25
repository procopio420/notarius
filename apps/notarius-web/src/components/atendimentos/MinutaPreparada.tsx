'use client'

import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type MinutaPreparada, type TextoModelo } from '@/lib/atendimentos'
import { ComparacaoMinuta } from './ComparacaoMinuta'
import { BibliotecaModelos } from './BibliotecaModelos'
import { RevisaoFinalDaMinuta } from './RevisaoFinalDaMinuta'
import { PosicoesModelo } from './PosicoesModelo'
import { BlocosModelo } from './BlocosModelo'
import { VinculacaoMinuta } from './VinculacaoMinuta'
import { RegrasRevisaoModelo } from './RegrasRevisaoModelo'
import { CamposQualificacaoModelo } from './CamposQualificacaoModelo'
import { useRascunhoSessao } from '@/lib/rascunhoSessao'

interface ModeloLocal { modelo: TextoModelo; motivo: string; versao: number; referencia: string | null }
interface EdicaoLocal { minuta_id: string; versao: number; corpo: string; motivo: string }
const modeloLocalValido = (v: unknown): v is ModeloLocal | null => v === null || !!v && typeof (v as ModeloLocal).modelo?.corpo === 'string' && typeof (v as ModeloLocal).motivo === 'string' && typeof (v as ModeloLocal).versao === 'number'
const edicoesValidas = (v: unknown): v is EdicaoLocal[] => Array.isArray(v) && v.every(e => !!e && typeof e.minuta_id === 'string' && typeof e.corpo === 'string' && typeof e.motivo === 'string' && typeof e.versao === 'number')

export function PreparacaoMinuta({ id, scope }: { id: string; scope: (string | undefined)[] }) {
  const modelLocal = useRascunhoSessao<ModeloLocal | null>(scope, 'modelo-minuta', null, modeloLocalValido)
  const editLocal = useRascunhoSessao<EdicaoLocal[]>(scope, 'edicoes-minuta', [], edicoesValidas)
  const attemptLocal = useRascunhoSessao(scope, 'envio-edicao-minuta', { payload: '', id: '' }, (v): v is { payload: string; id: string } => !!v && typeof (v as { payload?: unknown }).payload === 'string' && typeof (v as { id?: unknown }).id === 'string')
  const cache = useQueryClient()
  const models = useQuery({ queryKey: ['modelo-atendimento', ...scope], queryFn: () => atendimentosApi.modelos(id) })
  const state = useQuery({ queryKey: ['minuta-atendimento', ...scope], queryFn: () => atendimentosApi.redacao(id) })
  const [showModel, setShowModel] = useState(false)
  const [draft, setDraft] = useState<TextoModelo>({ corpo: '', representacao: '', observacoes: '' })
  const [approved, setApproved] = useState(false)
  const [reason, setReason] = useState('')
  const [expectedVersion, setExpectedVersion] = useState(0)
  const [referenceId, setReferenceId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<MinutaPreparada | null>(null)
  const [showSources, setShowSources] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editedText, setEditedText] = useState('')
  const [editReason, setEditReason] = useState('')
  const [discard, setDiscard] = useState(false)
  const editRetry = useRef<{ payload: string; id: string } | null>(null)
  const dirty = editing && editedText !== preview?.corpo
  const previewStale = !!preview && (preview.desatualizada || !!state.data?.versoes.find(m => m.id === preview.id)?.desatualizada)
  const latest = !!preview && state.data?.versoes[0]?.id === preview.id
  const livePreview = state.data?.versoes.find(m => m.id === preview?.id) || preview
  const reviewed = !!livePreview?.revisao_final?.texto_corresponde
  const saveModelLocal = modelLocal.save, modelReady = modelLocal.ready
  useEffect(() => {
    if (showModel && modelReady) saveModelLocal({ modelo: draft, motivo: reason, versao: expectedVersion, referencia: referenceId })
  }, [showModel, modelReady, saveModelLocal, draft, reason, expectedVersion, referenceId])
  const saveEditLocal = editLocal.save, editReady = editLocal.ready
  useEffect(() => {
    if (editing && preview && editReady) {
      const snapshot = { minuta_id: preview.id, versao: preview.versao, corpo: editedText, motivo: editReason }
      saveEditLocal(old => [...old.filter(e => e.minuta_id !== snapshot.minuta_id), snapshot])
    }
  }, [editing, preview, editReady, saveEditLocal, editedText, editReason])
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])
  function openPreview(item: MinutaPreparada) { setPreview(item); setEditing(false); setShowSources(false); setError('') }
  function closePreview() { if (busy) return; if (dirty) setDiscard(true); else { setPreview(null); setEditing(false); setError('') } }
  async function saveEdit() {
    if (!preview || busy) return
    const payload = { minuta_id: preview.id, versao_esperada: preview.versao, corpo: editedText, motivo: editReason.trim() }
    const serialized = JSON.stringify(payload)
    const clientId = editRetry.current?.payload === serialized ? editRetry.current.id : attemptLocal.value.payload === serialized && attemptLocal.value.id ? attemptLocal.value.id : crypto.randomUUID()
    editRetry.current = { payload: serialized, id: clientId }
    attemptLocal.save(editRetry.current)
    setBusy(true); setError('')
    try {
      const saved = await atendimentosApi.editarMinuta(id, { ...payload, client_id: clientId })
      const result = await atendimentosApi.redacao(id)
      cache.setQueryData(['minuta-atendimento', ...scope], result)
      const item = result.versoes.find(m => m.id === saved.id)
      if (item) { editLocal.save(old => old.filter(e => e.minuta_id !== preview.id)); attemptLocal.clear(); setPreview(item); setEditing(false); editRetry.current = null }
    } catch (err) { failure(err); void state.refetch() } finally { setBusy(false) }
  }
  async function download(format: 'pdf' | 'docx') {
    if (!preview || busy || editing) return
    setBusy(true); setError('')
    try {
      const blob = await atendimentosApi.exportarMinuta(id, preview.id, format)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `minuta-v${preview.versao}.${format}`; anchor.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      const data = (err as { response?: { data?: unknown } }).response?.data
      if (data instanceof Blob) {
        try { const details = JSON.parse(await data.text()); setError(Array.isArray(details) ? details.join(' ') : details.detail || 'Não foi possível exportar a versão salva.') } catch { setError('Não foi possível exportar. Confira se a versão continua atual.') }
      } else failure(err)
      void state.refetch()
    } finally { setBusy(false) }
  }
  const current = models.data?.versoes[0]

  function openModel() {
    const saved = modelLocal.value
    if (saved) { setDraft(saved.modelo); setReferenceId(saved.referencia); setExpectedVersion(saved.versao); setApproved(false); setReason(saved.motivo); setError(''); setShowModel(true); return }
    const data = current || models.data?.base
    if (!data) return
    setDraft({ corpo: data.corpo, representacao: data.representacao, observacoes: data.observacoes, registros_minuta: data.registros_minuta || [], campos_qualificacao: data.campos_qualificacao || [], campos_obrigatorios_ficha: data.campos_obrigatorios_ficha || [], dependencias_campos_ficha: data.dependencias_campos_ficha || [] })
    setReferenceId(current?.referencia_id || null)
    setExpectedVersion(current?.versao || 0); setApproved(false); setReason(''); setError(''); setShowModel(true)
  }
  function failure(err: unknown) {
    const data = (err as { response?: { data?: unknown } }).response?.data
    setError(Array.isArray(data) ? data.join(' ') : typeof data === 'object' && data && 'detail' in data ? String(data.detail) : 'Não foi possível confirmar a operação. Atualize antes de tentar novamente.')
  }
  async function saveModel() {
    setBusy(true); setError('')
    try {
      await atendimentosApi.salvarModelo(id, { ...draft, aprovado: approved, justificativa: reason.trim(), versao_esperada: expectedVersion, referencia_id: referenceId })
      await Promise.all(['modelo-atendimento', 'minuta-atendimento', 'conferencia-atendimento', 'ficha-atendimento', 'ficha-detalhada'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      setShowModel(false)
      modelLocal.clear()
    } catch (err) { failure(err) } finally { setBusy(false) }
  }
  async function prepare() {
    if (!state.data) return
    setBusy(true); setError('')
    try {
      const result = await atendimentosApi.prepararMinuta(id, state.data.assinatura)
      cache.setQueryData(['minuta-atendimento', ...scope], result)
      if (result.versoes[0]) openPreview(result.versoes[0])
    } catch (err) { failure(err); void state.refetch() } finally { setBusy(false) }
  }
  return <Stack spacing={1}>
    <VinculacaoMinuta key={scope.join(':')} id={id} scope={scope} />
    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
      <Button variant="outlined" onClick={openModel} disabled={!models.data || busy}>Revisar modelo</Button>
      <Button variant="contained" onClick={prepare} disabled={busy || !state.data?.pronto || state.isError}>{busy ? 'Preparando…' : 'Preparar minuta'}</Button>
      {state.data?.versoes[0] && <Button onClick={() => openPreview(state.data!.versoes[0])}>Abrir minuta v{state.data.versoes[0].versao}</Button>}
    </Stack>
    {modelLocal.value && <Alert severity="info">Há rascunho local do modelo. “Revisar modelo” retoma o texto, mantendo a versão de origem e sem recuperar aprovação.</Alert>}
    {editLocal.value.map(e => <Button key={e.minuta_id} onClick={() => { const item = state.data?.versoes.find(m => m.id === e.minuta_id); if (!item) { setError('Versão do rascunho indisponível. O texto local foi preservado.'); return } setPreview(item); setEditedText(e.corpo); setEditReason(e.motivo); setEditing(true); setError('') }}>Retomar edição local da minuta v{e.versao}, sem revisar ou assinar</Button>)}
    {(modelLocal.aviso || editLocal.aviso || attemptLocal.aviso) && <Alert severity="warning">{modelLocal.aviso || editLocal.aviso || attemptLocal.aviso}</Alert>}
    {models.isError || state.isError ? <Alert severity="error" action={<Button onClick={() => { void models.refetch(); void state.refetch() }}>Atualizar</Button>}>Não foi possível conferir o modelo e a minuta.</Alert> : <Typography variant="caption" color="text.secondary">{!state.data?.modelo_aprovado ? 'A escrevente precisa revisar e aprovar o modelo antes de preparar a minuta.' : state.data?.pendencias ? 'Modelo aprovado; falta resolver as pendências do atendimento.' : 'Modelo aprovado e verificações iniciais respondidas. A minuta ainda exigirá revisão.'}</Typography>}
    {state.data?.versoes[0]?.desatualizada && <Alert severity="warning">Os dados ou o modelo mudaram após a preparação. Confira as pendências e prepare uma nova versão.</Alert>}
    {state.data?.modelo_aprovado && !state.data.pronto && !state.data.pendencias && state.data.motivo_bloqueio && <Alert severity="warning">{state.data.motivo_bloqueio}</Alert>}
    {error && !showModel && <Alert severity="error">{error}</Alert>}
    <Dialog open={showModel} onClose={() => !busy && setShowModel(false)} fullWidth maxWidth="md"><DialogTitle>Modelo de compra e venda</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="warning">A base oferecida é uma estrutura inicial, não um padrão completo aprovado do cartório. O modelo não é fonte de pagamento realizado, consulta efetuada ou assinatura. Registre acontecimentos somente nos campos, com fonte e confirmação específica. A verificação automática de frases é limitada; revise todo o texto fixo antes de aprovar.</Alert>
        {models.data?.referencia && <Box>
          <Button disabled={busy} onClick={() => {
            setDraft({ ...models.data!.referencia.modelo }); setReferenceId(null); setApproved(false); setReason(''); setError('')
          }}>Usar estrutura da escritura enviada</Button>
          <Typography variant="body2">{models.data.referencia.aviso}</Typography>
          <Typography variant="caption">Ao salvar, os campos desta estrutura entram nas perguntas da conversa. As versões anteriores são preservadas.</Typography>
        </Box>}
        <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Estruturas complementares para revisar</Typography>
          <Alert severity="warning">Incluem posições para abertura, declarações, tributos, documentos, consultas e encerramento. Não são requisitos jurídicos ou modelos homologados. Carregar só altera este rascunho; não cria registros nem confirma dados.</Alert>
          {models.data?.referencias_complementares?.map(ref => <Button key={ref.variante} disabled={busy} onClick={() => { setDraft(ref.modelo); setApproved(false); setReferenceId(null); setReason(''); setError('') }}>Carregar {ref.nome}</Button>)}
        </Box>
        <BibliotecaModelos id={id} scope={scope} current={current}
          canPublish={JSON.stringify(draft.registros_minuta || []) === JSON.stringify(current?.registros_minuta || []) && JSON.stringify(draft.campos_obrigatorios_ficha || []) === JSON.stringify(current?.campos_obrigatorios_ficha || []) && JSON.stringify(draft.dependencias_campos_ficha || []) === JSON.stringify(current?.dependencias_campos_ficha || []) && !busy && !!current && draft.corpo === current.corpo && draft.representacao === current.representacao && draft.observacoes === current.observacoes && JSON.stringify(draft.campos_qualificacao || []) === JSON.stringify(current.campos_qualificacao || [])}
          onLoad={model => { setDraft({ corpo: model.corpo, representacao: model.representacao, observacoes: model.observacoes, registros_minuta: model.registros_minuta || [], campos_qualificacao: model.campos_qualificacao || [], campos_obrigatorios_ficha: model.campos_obrigatorios_ficha || [], dependencias_campos_ficha: model.dependencias_campos_ficha || [] }); setReferenceId(model.id); setApproved(false); setReason(''); setError('') }} />
        {referenceId && <Typography variant="caption">Texto baseado em um padrão da biblioteca. A aprovação deve ser feita para este atendimento.</Typography>}
        <Button disabled={busy || !models.data?.modelo_ficticio_estruturado} onClick={() => { setDraft(models.data!.modelo_ficticio_estruturado); setReferenceId(null); setApproved(false); setReason('DEMONSTRAÇÃO FICTÍCIA SEM HOMOLOGAÇÃO PROFISSIONAL') }}>Carregar modelo fictício com condições e repetições</Button>
        <Alert severity="warning">A redação e as regras profissionais dependem de homologação pela escrevente. O exemplo fictício serve somente para testes e não contém redação profissional aprovada.</Alert>
        <Typography variant="body2">{draft.registros_minuta?.length ? 'Blocos condicionais e repetições só entram conforme configuração explícita e dados confirmados. Use as posições configuradas e os campos da ficha, por exemplo {{vendedor1.nome}}. Cada marcador será substituído pelo valor confirmado daquele registro. Texto fora de blocos condicionais é fixo e precisa de revisão profissional.' : 'Modelo antigo por blocos: {{vendedores}}, {{compradores}}, {{imovel}}, {{preco}}, {{pagamento}}. Para usar a ficha separada, configure posições e substitua os marcadores pelo padrão posição.campo.'}</Typography>
        {!draft.registros_minuta?.length && <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Campos disponíveis para o modelo antigo</Typography>
          {models.data?.marcadores.map(field => <Typography variant="body2" key={field.chave}>{`{{${field.chave}}}`} — {field.rotulo}</Typography>)}
        </Box>}
        <TextField label="Texto fixo e campos do modelo" multiline minRows={10} value={draft.corpo} onChange={e => { setDraft({ ...draft, corpo: e.target.value }); setApproved(false) }} disabled={busy} slotProps={{ htmlInput: { maxLength: 60000 } }} />
        <TextField label={draft.registros_minuta?.length ? 'Bloco adicional de representação' : 'Bloco condicional de representação'} multiline minRows={3} value={draft.representacao} onChange={e => { setDraft({ ...draft, representacao: e.target.value }); setApproved(false) }} disabled={busy} helperText={draft.registros_minuta?.length ? "Blocos condicionais exigem configuração explícita. Use marcadores de posição.campo; não copie fatos do exemplo." : "Só entra quando representação tiver informação confirmada. Use {{representacao}}."} slotProps={{ htmlInput: { maxLength: 10000 } }} />
        <TextField label={draft.registros_minuta?.length ? 'Bloco adicional de observações' : 'Bloco condicional de observações'} multiline minRows={3} value={draft.observacoes} onChange={e => { setDraft({ ...draft, observacoes: e.target.value }); setApproved(false) }} disabled={busy} helperText={draft.registros_minuta?.length ? "Blocos condicionais exigem configuração explícita. Use marcadores de posição.campo." : "Só entra quando houver observações confirmadas. Use {{observacoes}}."} slotProps={{ htmlInput: { maxLength: 10000 } }} />
        <TextField label="Motivo ou descrição da revisão do modelo" multiline minRows={2} value={reason} onChange={e => setReason(e.target.value)} required disabled={busy} slotProps={{ htmlInput: { maxLength: 2000 } }} />
        <BlocosModelo value={draft} disabled={busy} onChange={v => { setDraft(v); setApproved(false) }} />
        <PosicoesModelo key={`posicoes:${scope.join(':')}`} id={id} scope={scope} value={draft} disabled={busy} onChange={v => { setDraft(v); setApproved(false) }} />
        <RegrasRevisaoModelo key={`regras:${scope.join(':')}`} id={id} scope={scope} value={draft} disabled={busy} onChange={v => { setDraft(v); setApproved(false) }} />
        <CamposQualificacaoModelo value={draft.campos_qualificacao || []} disabled={busy} onChange={fields => { setDraft({ ...draft, campos_qualificacao: fields }); setApproved(false) }} />
        <FormControlLabel control={<Checkbox checked={approved} onChange={e => setApproved(e.target.checked)} disabled={busy} />} label={draft.registros_minuta?.length ? 'Revisei integralmente o padrão, suas posições e vínculos. Retirei os fatos do exemplo: pagamento, consultas e assinaturas exigem dados confirmados com fonte. Aprovo esta versão do modelo para este atendimento.' : 'Revisei o texto e aprovo esta versão do modelo para este atendimento.'} />
        <Typography variant="caption">Sem aprovação, o modelo fica salvo em rascunho e bloqueia a preparação. Cada alteração cria uma versão nova.</Typography>
        {models.data?.versoes.length ? <Box><Typography fontWeight={600}>Versões anteriores</Typography>{models.data.versoes.map(m => <Button key={m.id} disabled={busy} onClick={() => { setDraft({ corpo: m.corpo, representacao: m.representacao, observacoes: m.observacoes, registros_minuta: m.registros_minuta || [], campos_qualificacao: m.campos_qualificacao || [], campos_obrigatorios_ficha: m.campos_obrigatorios_ficha || [], dependencias_campos_ficha: m.dependencias_campos_ficha || [] }); setReferenceId(m.referencia_id || null); setApproved(false) }}>Carregar v{m.versao} · {m.aprovado ? 'aprovada' : 'rascunho'}</Button>)}</Box> : null}
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => { setShowModel(false); setApproved(false); modelLocal.clear() }}>Descartar só o rascunho local</Button><Button disabled={busy} onClick={() => setShowModel(false)}>Voltar e manter rascunho</Button><Button variant="contained" onClick={saveModel} disabled={busy || !reason.trim() || !draft.corpo.trim()}>{busy ? 'Salvando…' : approved ? 'Salvar modelo aprovado' : 'Salvar rascunho do modelo'}</Button></DialogActions>
    </Dialog>
    <Dialog open={!!preview} onClose={closePreview} fullWidth maxWidth="md"><DialogTitle>Minuta para revisão · v{preview?.versao}</DialogTitle>
      <DialogContent><Stack spacing={2}>
        <Alert severity="info">Modelo v{preview?.modelo_versao}. Preenchimento literal dos dados confirmados, sem redação livre da IA. Confira integralmente antes de usar.</Alert>
        {previewStale && <Alert severity="warning">Esta versão está desatualizada. Prepare outra versão após revisar as alterações. Exportação bloqueada.</Alert>}
        {!latest && <Alert severity="info">Versão histórica. Abra a versão mais recente para editar ou exportar.</Alert>}
        {preview?.tipo === 'editada' && <Alert severity="info">Texto editado pela escrevente. As alterações manuais não foram conferidas automaticamente. Motivo: {preview.motivo}</Alert>}
        {editing ? <Stack spacing={2}>
          <TextField label="Editar texto da minuta" multiline minRows={14} value={editedText} onChange={e => setEditedText(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength: 150000 } }} helperText="Salve uma nova versão para manter as alterações. Este editor não atualiza a ficha; correções de dados devem ser feitas na ficha e usadas em nova preparação." />
          <TextField label="Motivo da edição" multiline minRows={2} value={editReason} onChange={e => setEditReason(e.target.value)} disabled={busy} required slotProps={{ htmlInput: { maxLength: 2000 } }} />
        </Stack> : <Typography component="pre" sx={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{preview?.corpo}</Typography>}
        <Stack direction="row" gap={1} flexWrap="wrap">
          {preview && <ComparacaoMinuta key={preview.id} id={id} scope={scope} atual={preview} versoes={state.data?.versoes || []} disabled={busy || editing} />}
          {!editing && <Button variant="outlined" disabled={busy || !latest || previewStale || !state.data?.pronto} onClick={() => { setEditedText(preview?.corpo || ''); setEditReason(''); setEditing(true); setError('') }}>Editar minuta</Button>}
          {editing && <Button variant="contained" onClick={saveEdit} disabled={busy || !dirty || !editedText.trim() || !editReason.trim() || previewStale}>Salvar nova versão</Button>}
          <Button onClick={() => download('docx')} disabled={busy || editing || !latest || previewStale || !state.data?.pronto || !reviewed}>Baixar Word</Button>
          <Button onClick={() => download('pdf')} disabled={busy || editing || !latest || previewStale || !state.data?.pronto || !reviewed}>Baixar PDF</Button>
        </Stack>
        {livePreview && <RevisaoFinalDaMinuta key={livePreview.id} id={id} minuta={livePreview} disabled={busy || editing || !latest || previewStale || !state.data?.pronto} />}
        {error && <Alert severity="error">{error}</Alert>}
        <Button sx={{ alignSelf: 'flex-start' }} onClick={() => setShowSources(!showSources)}>{showSources ? 'Ocultar dados utilizados' : 'Conferir dados utilizados'}</Button>
        {showSources && Object.entries(preview?.dados || {}).map(([key, data]) => <Box key={key} sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
          {data.objeto_id && <Typography variant="body2">Registro {data.tipo} · {data.objeto_id} · vinculação {data.vinculacao_id}</Typography>}
          <Typography fontWeight={600}>{key} · versão {data.versao} · {data.situacao}</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{data.valor}</Typography>
          {data.valor_original !== undefined && data.valor_original !== data.valor && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Valor original preservado: {data.valor_original}</Typography>}
          <Typography variant="caption">Origem: {data.origem?.tipo === 'documento' ? `${data.origem.arquivo} · página ${data.origem.pagina} · leitura ${data.origem.leitura_versao ?? 'não identificada'}${data.origem.canal === 'ocr' ? ' · OCR' : ' · texto'}` : data.origem?.tipo === 'mensagem' ? `mensagem ${data.origem.mensagem_id}` : 'registro manual'}</Typography>
          {data.ocorrencias && <Typography variant="caption">{preview?.ocorrencias_correspondem_texto === false ? "Posições no preenchimento da versão de base; o texto editado exige revisão integral." : data.ocorrencias.length === 0 ? "Dado utilizado para avaliar uma condição configurada, sem inserção literal no texto." : `Inserções no texto: ${data.ocorrencias.map(o => `${o.bloco}: ${o.inicio}–${o.fim}`).join('; ')}`}</Typography>}
          {data.decisoes_blocos?.map(d => <Alert key={d.chave} severity="info">{preview?.ocorrencias_correspondem_texto === false ? 'Decisão no preenchimento de base; a edição manual exige nova revisão. ' : ''}Bloco {d.chave}: {d.incluido ? 'incluído' : 'omitido'} pela condição configurada no modelo v{d.modelo_versao}. Campo {d.configuracao.campo}, valor confirmado: {d.valor_confirmado}. Alternativas previstas: {d.configuracao.permitidos.join('; ')}. Inclui quando: {d.configuracao.incluir.join('; ')}. Decisão do modelo revisado pela escrevente; não foi escolhida pela IA.</Alert>)}
          {data.ocorrencias?.filter(o => o.repeticao).map((o,i) => <Typography key={i} variant="caption">Repetição {o.repeticao!.bloco} · posição {o.repeticao!.posicao} · item {o.repeticao!.indice}</Typography>)}
          {data.origem?.trecho && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>Trecho: {data.origem.trecho}</Typography>}
        </Box>)}
        <Typography fontWeight={600}>Versões salvas</Typography><Stack direction="row" gap={1} flexWrap="wrap">{state.data?.versoes.map(m => <Button key={m.id} disabled={busy || dirty} onClick={() => openPreview(m)}>v{m.versao}{m.tipo === 'editada' ? ' · editada' : ''}{m.desatualizada ? ' · desatualizada' : ''}</Button>)}</Stack>
      </Stack></DialogContent><DialogActions><Button onClick={closePreview} disabled={busy}>Voltar à conversa</Button></DialogActions>
    </Dialog>
    <Dialog open={discard} onClose={() => setDiscard(false)}><DialogTitle>Há alterações não salvas</DialogTitle><DialogContent>Salve uma nova versão para manter suas alterações.</DialogContent><DialogActions><Button onClick={() => setDiscard(false)}>Continuar editando</Button><Button color="error" onClick={() => { if (preview) editLocal.save(old => old.filter(e => e.minuta_id !== preview.id)); setDiscard(false); setPreview(null); setEditing(false); setError('') }}>Descartar alterações</Button></DialogActions></Dialog>
  </Stack>
}
