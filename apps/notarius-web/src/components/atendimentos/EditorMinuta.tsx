'use client'

import { useEffect, useId, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TextField, Typography, useMediaQuery, useTheme } from '@mui/material'
import { Download } from 'lucide-react'
import { atendimentosApi, type EstiloMinuta, type FormatacaoMinuta, type MinutaPreparada } from '@/lib/atendimentos'
import { useRascunhoSessao } from '@/lib/rascunhoSessao'
import { ajustarFormatacao, alternarEstilo, estilos, trechosFormatados } from '@/lib/formatacaoMinuta'
import { origemDaMinuta } from '@/lib/chatAtendimento'
import { ComparacaoMinuta } from './ComparacaoMinuta'
import { RevisaoFinalDaMinuta } from './RevisaoFinalDaMinuta'

interface EdicaoLocal { minuta_id: string; versao: number; corpo: string; motivo: string; formatacao?: FormatacaoMinuta }
const semFormatacao: FormatacaoMinuta = {}
const nomesEstilos = { negrito: 'Negrito', italico: 'Itálico', sublinhado: 'Sublinhado' }
const edicoesValidas = (v: unknown): v is EdicaoLocal[] => Array.isArray(v) && v.every(e => !!e && typeof e.minuta_id === 'string' && typeof e.corpo === 'string' && typeof e.motivo === 'string' && typeof e.versao === 'number'
  && (e.formatacao === undefined || (e.formatacao && estilos.every(estilo => e.formatacao[estilo] === undefined ||
    (Array.isArray(e.formatacao[estilo]) && e.formatacao[estilo].every((r: unknown) => Array.isArray(r) && r.length === 2 && r.every(Number.isInteger)))))))

function renderTrechos(trechos: ReturnType<typeof trechosFormatados>[number]) {
  return trechos.map(({ texto, estilos }, index) => estilos.length ? <span key={index} style={{
    fontWeight: estilos.includes('negrito') ? 700 : undefined,
    fontStyle: estilos.includes('italico') ? 'italic' : undefined,
    textDecoration: estilos.includes('sublinhado') ? 'underline' : undefined,
  }}>{texto}</span> : texto)
}

export function EditorMinuta({ id, scope, inicial, onClose }: {
  id: string
  scope: (string | undefined)[]
  inicial: MinutaPreparada
  onClose: () => void
}) {
  const titleId = useId()
  const theme = useTheme()
  const mobile = useMediaQuery(theme.breakpoints.down('sm'))
  const [busca, setBusca] = useState('')
  const [ocorrencia, setOcorrencia] = useState(0)
  const [conflito, setConflito] = useState(false)
  const editInput = useRef<HTMLTextAreaElement>(null)
  const resultadoBusca = useRef<HTMLElement>(null)
  const editLocal = useRascunhoSessao<EdicaoLocal[]>(scope, 'edicoes-minuta', [], edicoesValidas)
  const attemptLocal = useRascunhoSessao(scope, 'envio-edicao-minuta', { payload: '', id: '' }, (v): v is { payload: string; id: string } => !!v && typeof (v as { payload?: unknown }).payload === 'string' && typeof (v as { id?: unknown }).id === 'string')
  const cache = useQueryClient()
  const state = useQuery({ queryKey: ['minuta-atendimento', ...scope], queryFn: () => atendimentosApi.redacao(id) })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(inicial)
  const [showSources, setShowSources] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editedText, setEditedText] = useState('')
  const [editedFormat, setEditedFormat] = useState<FormatacaoMinuta>(semFormatacao)
  const [editReason, setEditReason] = useState('')
  const [confirmacoes, setConfirmacoes] = useState<string[]>([])
  const [discard, setDiscard] = useState(false)
  const editRetry = useRef<{ payload: string; id: string } | null>(null)
  const dirty = editing && (editedText !== preview.corpo || estilos.some(estilo =>
    JSON.stringify(editedFormat[estilo] || []) !== JSON.stringify(preview.formatacao?.[estilo] || [])))
  const previewStale = !!preview && (preview.desatualizada || !!state.data?.versoes.find(m => m.id === preview.id)?.desatualizada)
  const latest = !!preview && state.data?.versoes[0]?.id === preview.id
  const comparisonTarget = editing && !latest ? state.data?.versoes[0] || preview : preview
  const comparisonBase = comparisonTarget.id !== preview.id ? preview.id : undefined
  const livePreview = state.data?.versoes.find(m => m.id === preview?.id) || preview
  const reviewed = !!livePreview?.revisao_final?.texto_corresponde
  const declaracoes = preview.assistencia?.pendencias.filter(item => item.confirmacao ?? item.campo.startsWith('fiel_conferencia_')) || []
  const podeEditar = !!preview.assistencia || !!state.data?.pronto
  const podeRevisar = preview.assistencia ? !preview.corpo.includes('[PENDÊNCIA · ') && !declaracoes.length : !!state.data?.pronto
  const saveEditLocal = editLocal.save, editReady = editLocal.ready
  useEffect(() => {
    if (editing && preview && editReady) {
      const snapshot = { minuta_id: preview.id, versao: preview.versao, corpo: editedText, motivo: editReason, formatacao: editedFormat }
      saveEditLocal(old => [...old.filter(e => e.minuta_id !== snapshot.minuta_id), snapshot])
    }
  }, [editing, preview, editReady, saveEditLocal, editedText, editReason, editedFormat])
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])
  useEffect(() => {
    resultadoBusca.current?.scrollIntoView?.({ block: 'nearest' })
  }, [busca, ocorrencia])

  function openPreview(item: MinutaPreparada) {
    setPreview(item)
    setConfirmacoes([])
    setEditing(false)
    setShowSources(false)
    setError('')
    setConflito(false)
    setBusca('')
    setOcorrencia(0)
  }

  function closePreview() {
    if (busy) return
    if (dirty) setDiscard(true)
    else onClose()
  }

  function retomar(edicao: EdicaoLocal) {
    const item = state.data?.versoes.find(m => m.id === edicao.minuta_id)
    if (!item) {
      setError('A versão de origem não está disponível. Seu texto foi preservado nesta aba.')
      return
    }
    openPreview(item)
    setEditedText(edicao.corpo)
    setEditedFormat(edicao.formatacao ?? (edicao.corpo === item.corpo ? item.formatacao ?? semFormatacao : semFormatacao))
    setEditReason(edicao.motivo)
    setEditing(true)
  }

  function changeText(text: string) {
    setEditedFormat(ajustarFormatacao(editedText, text, editedFormat))
    setEditedText(text)
  }

  function formatSelection(estilo: EstiloMinuta) {
    const input = editInput.current
    if (!input) return
    const { selectionStart, selectionEnd } = input
    if (selectionStart === selectionEnd) {
      setError('Selecione o trecho que deseja formatar.')
      input.focus()
      return
    }
    const format = alternarEstilo(editedFormat, estilo, selectionStart, selectionEnd)
    if (!format) { setError('O limite é de 500 trechos por estilo.'); return }
    setEditedFormat(format)
    setError('')
    input.focus()
  }

  function inserirParagrafo() {
    const input = editInput.current
    if (!input) return
    const { selectionEnd } = input
    if (editedText.length + 2 > 150000) return
    changeText(editedText.slice(0, selectionEnd) + '\n\n' + editedText.slice(selectionEnd))
    requestAnimationFrame(() => {
      input.focus()
      input.setSelectionRange(selectionEnd + 2, selectionEnd + 2)
    })
  }
  async function saveEdit() {
    if (busy || !latest || previewStale || conflito || !podeEditar) return
    const payload = { minuta_id: preview.id, versao_esperada: preview.versao, corpo: editedText, formatacao: editedFormat, motivo: editReason.trim() }
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
      if (item) { editLocal.save(old => old.filter(e => e.minuta_id !== preview.id)); attemptLocal.clear(); openPreview(item); editRetry.current = null }
    } catch (err) {
      if ((err as { response?: { status?: number } }).response?.status === 409) {
        setConflito(true)
        setError('A minuta ou os dados mudaram. Seu texto foi preservado. Compare as versões antes de retomar.')
      } else failure(err)
      void state.refetch()
    } finally { setBusy(false) }
  }
  async function salvarDeclaracoes() {
    if (busy || editing || !latest || previewStale || !confirmacoes.length) return
    let corpo = preview.corpo
    let formatacao = preview.formatacao ?? semFormatacao
    for (const item of declaracoes.filter(item => confirmacoes.includes(item.campo))) {
      const marcador = `[PENDÊNCIA · ${item.rotulo}] `
      let inicio = corpo.indexOf(marcador)
      while (inicio !== -1) {
        const novo = corpo.slice(0, inicio) + corpo.slice(inicio + marcador.length)
        formatacao = ajustarFormatacao(corpo, novo, formatacao)
        corpo = novo
        inicio = corpo.indexOf(marcador, inicio)
      }
    }
    const payload = { minuta_id: preview.id, versao_esperada: preview.versao, corpo, formatacao,
      confirmacoes: [...confirmacoes].sort(), motivo: 'Declarações do caso conferidas no editor da minuta.' }
    const serialized = JSON.stringify(payload)
    const clientId = editRetry.current?.payload === serialized ? editRetry.current.id : crypto.randomUUID()
    editRetry.current = { payload: serialized, id: clientId }
    setBusy(true); setError('')
    try {
      const saved = await atendimentosApi.editarMinuta(id, { ...payload, client_id: clientId })
      const result = await atendimentosApi.redacao(id)
      cache.setQueryData(['minuta-atendimento', ...scope], result)
      const item = result.versoes.find(m => m.id === saved.id)
      if (item) { openPreview(item); editRetry.current = null }
    } catch (err) {
      failure(err)
      void state.refetch()
    } finally { setBusy(false) }
  }
  async function download(format: 'pdf' | 'pdfa' | 'docx') {
    if (!preview || busy || editing) return
    setBusy(true); setError('')
    try {
      const blob = await atendimentosApi.exportarMinuta(id, preview.id, format)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = format === 'pdfa' ? `minuta-v${preview.versao}-pdfa.pdf` : `minuta-v${preview.versao}.${format}`; anchor.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      const data = (err as { response?: { data?: unknown } }).response?.data
      if (data instanceof Blob) {
        try { const details = JSON.parse(await data.text()); setError(Array.isArray(details) ? details.join(' ') : details.detail || 'Não foi possível exportar a versão salva.') } catch { setError('Não foi possível exportar. Confira se a versão continua atual.') }
      } else failure(err)
      void state.refetch()
    } finally { setBusy(false) }
  }
  function failure(err: unknown) {
    const data = (err as { response?: { data?: unknown } }).response?.data
    setError(Array.isArray(data) ? data.join(' ') : typeof data === 'object' && data && 'detail' in data ? String(data.detail) : 'Não foi possível confirmar a operação. Atualize antes de tentar novamente.')
  }
  const texto = preview.corpo
  const partes = busca.trim()
    ? texto.split(new RegExp('(' + busca.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'))
    : [texto]
  const totalResultados = (partes.length - 1) / 2
  const resultadoAtual = Math.min(ocorrencia, Math.max(0, totalResultados - 1))
  const formatted = trechosFormatados(partes, preview.formatacao ?? semFormatacao)

  return <>
    <Dialog open onClose={closePreview} fullWidth fullScreen={mobile} maxWidth="lg" aria-labelledby={titleId}><DialogTitle id={titleId}><Stack direction="row" alignItems="center" justifyContent="space-between" gap={2}><Box><Typography component="span" sx={{ display: 'block', fontSize: 12, color: 'text.secondary', fontWeight: 600, letterSpacing: '.06em', mb: .4 }}>COMPRA E VENDA</Typography>Minuta · versão {preview?.versao}</Box><Chip size="small" label={reviewed && !previewStale ? 'Revisão registrada' : 'Revisão pendente'} variant="outlined" /></Stack></DialogTitle>
      <DialogContent dividers><Stack spacing={2}>
        {preview.assistencia && <Alert severity="info">Confira os dados inseridos e as declarações sinalizadas antes de registrar a revisão.</Alert>}
        {preview.assistencia?.ocr && <Alert severity="warning">A minuta usa leitura automática de imagens. Compare principalmente os nomes, CPFs e números com os originais.</Alert>}
        {previewStale && <Alert severity="warning">Esta versão está desatualizada. Prepare outra versão após revisar as alterações. Exportação bloqueada.</Alert>}
        {state.isLoading && <Typography role="status">Consultando as versões salvas…</Typography>}
        {state.isError && <Alert severity="error" action={<Button onClick={() => void state.refetch()}>Atualizar</Button>}>Não foi possível conferir a versão mais recente.</Alert>}
        {state.data && !latest && <Alert severity="info">Versão histórica. Abra a versão mais recente para editar ou exportar.</Alert>}
        {preview?.tipo === 'editada' && <Alert severity="info">Texto editado pela escrevente. As alterações manuais não foram conferidas automaticamente. Motivo: {preview.motivo}</Alert>}
        {(editLocal.aviso || attemptLocal.aviso) && <Alert severity="warning">{editLocal.aviso || attemptLocal.aviso}</Alert>}
        {!editing && editLocal.value.map(edicao => <Button key={edicao.minuta_id} size="small" sx={{ alignSelf: 'flex-start' }} onClick={() => retomar(edicao)}>Retomar edição local da v{edicao.versao}</Button>)}
        {editing && (comparisonBase || conflito) && <Alert severity="warning">Sua edição permanece aberta. {comparisonBase ? 'Compare com a versão mais recente antes de fazer novos ajustes.' : 'Confira os dados do atendimento e atualize as versões antes de retomar.'}</Alert>}
        {editing ? <Stack spacing={2}>
          <Stack direction="row" flexWrap="wrap" gap={.5} aria-label="Formatação da minuta">
            {estilos.map(estilo => <Button key={estilo} size="small" disabled={busy} onMouseDown={event => event.preventDefault()} onClick={() => formatSelection(estilo)}>{nomesEstilos[estilo]}</Button>)}
            <Button size="small" disabled={busy} onClick={inserirParagrafo}>Inserir parágrafo</Button>
          </Stack>
          <TextField inputRef={editInput} label="Editar texto da minuta" multiline minRows={14} value={editedText} onChange={e => changeText(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength: 150000 } }} helperText="Selecione um trecho para formatar. Corrija dados do atendimento na ficha." />
          {!!Object.keys(editedFormat).length && <Box component="details" open>
            <Typography component="summary" sx={{ cursor: 'pointer' }}>Prévia da formatação</Typography>
            <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontFamily: 'Georgia, serif', maxHeight: 220, overflow: 'auto' }}>
              {renderTrechos(trechosFormatados([editedText], editedFormat)[0])}
            </Typography>
          </Box>}
          <TextField label="Motivo da edição" multiline minRows={2} value={editReason} onChange={e => setEditReason(e.target.value)} disabled={busy} required slotProps={{ htmlInput: { maxLength: 2000 } }} />
        </Stack> : <>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
            <TextField size="small" label="Buscar no texto da minuta" value={busca} onChange={e => { setBusca(e.target.value); setOcorrencia(0) }} slotProps={{ htmlInput: { maxLength: 200 } }} />
            {!!busca.trim() && <Typography variant="body2" role="status">{totalResultados ? `${resultadoAtual + 1} de ${totalResultados}` : 'Nenhum resultado'}</Typography>}
            {totalResultados > 1 && <Button size="small" onClick={() => setOcorrencia((resultadoAtual + 1) % totalResultados)}>Próximo resultado</Button>}
          </Stack>
          <Box sx={{ bgcolor: '#f7f8f4', p: { xs: 1.5, sm: 3 }, borderRadius: 2 }}><Typography component="pre" sx={{ fontFamily: 'Georgia, serif', color: '#29372f', fontSize: 16, lineHeight: 1.9, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', bgcolor: '#fff', border: '1px solid #e3e8e1', boxShadow: '0 8px 28px #203c3506', borderRadius: 1, p: { xs: 2, sm: 5 }, maxWidth: 820, mx: 'auto', my: 0 }}>{formatted.map((trechos, i) => i % 2 === 0 ? <Box key={i} component="span">{renderTrechos(trechos)}</Box> : <mark key={i} ref={(i - 1) / 2 === resultadoAtual ? resultadoBusca : undefined}>{renderTrechos(trechos)}</mark>)}</Typography></Box>
        </>}
        <Stack direction="row" gap={1} flexWrap="wrap">
          <ComparacaoMinuta key={`${preview.id}:${comparisonTarget.id}`} id={id} scope={scope} atual={comparisonTarget} referenciaInicial={comparisonBase} versoes={state.data?.versoes || []} disabled={busy || (editing && !comparisonBase)} />
          {!editing && <Button variant="outlined" disabled={busy || !latest || previewStale || !podeEditar} onClick={() => { setEditedText(preview.corpo); setEditedFormat(preview.formatacao ?? semFormatacao); setEditReason(''); setEditing(true); setError('') }}>Editar minuta</Button>}
          {editing && <Button variant="contained" onClick={saveEdit} disabled={busy || !dirty || !editedText.trim() || !editReason.trim() || previewStale || !latest || conflito || !podeEditar}>Salvar nova versão</Button>}
          <Button variant="outlined" startIcon={<Download size={16} />} onClick={() => download('docx')} disabled={busy || editing || !latest || previewStale || !podeRevisar || !reviewed}>Baixar Word</Button>
          <Button variant="outlined" startIcon={<Download size={16} />} onClick={() => download('pdf')} disabled={busy || editing || !latest || previewStale || !podeRevisar || !reviewed}>Baixar PDF</Button>
          <Button variant="outlined" startIcon={<Download size={16} />} onClick={() => download('pdfa')} disabled={busy || editing || !latest || previewStale || !podeRevisar || !reviewed}>Baixar PDF/A</Button>
        </Stack>
        {preview.assistencia && (() => {
          const body = editing ? editedText : preview.corpo
          const pending = preview.assistencia.pendencias.filter(item => !declaracoes.includes(item) && body.includes(`[PENDÊNCIA · ${item.rotulo}]`))
          if (!pending.length) return null
          return <Box component="details" open>
            <Typography component="summary" sx={{ cursor: 'pointer', fontWeight: 650 }}>{pending.length} {pending.length === 1 ? 'trecho para conferir' : 'trechos para conferir'}</Typography>
            {pending.map(item => <Box key={item.campo} sx={{ mt: 1.25 }}>
              <Typography variant="body2"><strong>{item.rotulo}.</strong> {item.motivo}</Typography>
              {item.alternativas.map(({ valor, origem }, index) => {
                const fonte = origemDaMinuta(origem)
                return <Box key={index} sx={{ ml: 2, my: .75, overflowWrap: 'anywhere' }}>
                  <Typography variant="body2">{valor}</Typography>
                  {fonte?.tipo === 'documento' && <Typography variant="caption">{fonte.arquivo}, página {fonte.pagina}</Typography>}
                  {editing && <Button size="small" disabled={busy} onClick={() => changeText(editedText.replaceAll(`[PENDÊNCIA · ${item.rotulo}]`, () => valor))}>Usar este trecho</Button>}
                </Box>
              })}
            </Box>)}
          </Box>
        })()}
        {!!declaracoes.length && <Box component="details" open>
          <Typography component="summary" sx={{ cursor: 'pointer', fontWeight: 650 }}>Declarações a conferir</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ my: 1 }}>Marque só as declarações confirmadas para este caso.</Typography>
          <Stack spacing={.5} alignItems="flex-start">
            {declaracoes.map(item => <FormControlLabel key={item.campo} label={item.rotulo} control={<Checkbox
              checked={confirmacoes.includes(item.campo)} disabled={busy || editing || !latest || previewStale}
              onChange={(_, checked) => setConfirmacoes(old => checked ? [...old, item.campo] : old.filter(campo => campo !== item.campo))} />} />)}
            <Button onClick={() => void salvarDeclaracoes()} variant="outlined" disabled={!confirmacoes.length || busy || editing || !latest || previewStale}>Salvar declarações conferidas</Button>
          </Stack>
        </Box>}
        {livePreview && <RevisaoFinalDaMinuta key={livePreview.id} id={id} minuta={livePreview} disabled={busy || editing || !latest || previewStale || !podeRevisar} />}
        {error && <Alert severity="error">{error}</Alert>}
        <Button sx={{ alignSelf: 'flex-start' }} onClick={() => setShowSources(!showSources)}>{showSources ? 'Ocultar dados utilizados' : 'Conferir dados utilizados'}</Button>
        {showSources && Object.entries(preview?.dados || {}).map(([key, data]) => {
          const origem = origemDaMinuta(data.origem)
          return <Box key={key} sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
          {data.objeto_id && <Typography variant="body2">Registro {data.tipo} · {data.objeto_id} · vinculação {data.vinculacao_id}</Typography>}
          <Typography fontWeight={600}>{key} · versão {data.versao} · {data.situacao}</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{data.valor}</Typography>
          {data.valor_original !== undefined && data.valor_original !== data.valor && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Valor original preservado: {data.valor_original}</Typography>}
          <Typography variant="caption">Origem: {origem?.tipo === 'documento' ? `${origem.arquivo} · página ${origem.pagina} · leitura ${origem.leitura_versao ?? 'não identificada'}${origem.canal === 'ocr' ? ' · OCR' : ' · texto'}` : origem?.tipo === 'mensagem' ? `mensagem ${origem.mensagem_id}` : origem?.tipo === 'manual' ? 'registro manual' : 'origem não registrada'}</Typography>
          {data.ocorrencias && <Typography variant="caption">{preview?.ocorrencias_correspondem_texto === false ? "Posições no preenchimento da versão de base; o texto editado exige revisão integral." : data.ocorrencias.length === 0 ? "Dado utilizado para avaliar uma condição configurada, sem inserção literal no texto." : `Inserções no texto: ${data.ocorrencias.map(o => `${o.bloco}: ${o.inicio}–${o.fim}`).join('; ')}`}</Typography>}
          {data.decisoes_blocos?.map(d => <Alert key={d.chave} severity="info">{preview?.ocorrencias_correspondem_texto === false ? 'Decisão no preenchimento de base; a edição manual exige nova revisão. ' : ''}Bloco {d.chave}: {d.incluido ? 'incluído' : 'omitido'} pela condição configurada no modelo v{d.modelo_versao}. Campo {d.configuracao.campo}, valor confirmado: {d.valor_confirmado}. Alternativas previstas: {d.configuracao.permitidos.join('; ')}. Inclui quando: {d.configuracao.incluir.join('; ')}. Decisão do modelo revisado pela escrevente; não foi escolhida pela IA.</Alert>)}
          {data.ocorrencias?.filter(o => o.repeticao).map((o,i) => <Typography key={i} variant="caption">Repetição {o.repeticao!.bloco} · posição {o.repeticao!.posicao} · item {o.repeticao!.indice}</Typography>)}
          {origem?.trecho && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>Trecho: {origem.trecho}</Typography>}
        </Box>})}
        <Typography fontWeight={600}>Versões salvas</Typography><Stack direction="row" gap={1} flexWrap="wrap">{state.data?.versoes.map(m => <Button key={m.id} disabled={busy || dirty} onClick={() => openPreview(m)}>v{m.versao}{m.tipo === 'editada' ? ' · editada' : ''}{m.desatualizada ? ' · desatualizada' : ''}</Button>)}</Stack>
      </Stack></DialogContent><DialogActions><Button onClick={closePreview} disabled={busy}>Fechar minuta</Button></DialogActions>
    </Dialog>
    <Dialog open={discard} onClose={() => setDiscard(false)}><DialogTitle>Há alterações não salvas</DialogTitle><DialogContent>O texto pode ficar guardado nesta aba para você retomar depois.</DialogContent><DialogActions><Button onClick={() => setDiscard(false)}>Continuar editando</Button><Button onClick={onClose}>Fechar e manter edição</Button><Button color="error" onClick={() => { if (preview) editLocal.save(old => old.filter(e => e.minuta_id !== preview.id)); setDiscard(false); onClose() }}>Descartar alterações</Button></DialogActions></Dialog>
  </>
}
