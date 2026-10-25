'use client'
import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography, Box } from '@mui/material'
import { api } from '@/lib/api'
import { fichaDetalhadaApi } from '@/lib/fichaDetalhada'
import { ComparacaoFontes, FontesLadoALado, type EvidenciaComparada } from './ComparacaoFontes'

interface Issue { id: string; chave: string; titulo: string; pergunta: string; objeto_id: string | null; campo: string; tipo: string; situacao: string; assinatura: string; versao: number; acoes: string[]; contexto: Record<string, unknown>; historico: { versao: number; situacao: string; autor: string; motivo: string; data: string; resolucao?: { valor_escolhido?: string; campo_opcional_sem_uso?: boolean; evidencias_consideradas?: EvidenciaComparada[] } }[] }
interface Props { id: string; scope: (string | undefined)[]; open: boolean; onClose: () => void; inicial?: string | null }
export function PendenciasFicha(props: Props) { return <ConteudoPendenciasFicha key={[props.id, ...props.scope].join(':')} {...props} /> }
function ConteudoPendenciasFicha({ id, scope, open, onClose, inicial }: Props) {
  const cache = useQueryClient()
  const query = useQuery({ queryKey: ['pendencias-ficha', id, ...scope], enabled: open, queryFn: async (): Promise<Issue[]> => (await api.post(`/atendimentos/${id}/pendencias-ficha/`, { operacao: 'atualizar' })).data.pendencias })
  const sheet = useQuery({ queryKey: ['ficha-detalhada', ...scope], enabled: open, queryFn: () => fichaDetalhadaApi.get(id) })
  const [selected, setSelected] = useState<Issue | null>(null)
  const [comparing, setComparing] = useState(false), [evidenceIds, setEvidenceIds] = useState<string[]>([])
  const [reason, setReason] = useState(''), [action, setAction] = useState(''), [refs, setRefs] = useState<string[]>([])
  const [confirmed, setConfirmed] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const [adding, setAdding] = useState(false), [object, setObject] = useState(''), [field, setField] = useState(''), [question, setQuestion] = useState('')
  const retry = useRef<{ hash: string; id: string } | null>(null)
  function choose(p: Issue) { setSelected(p); setComparing(false); setEvidenceIds([]); setAdding(false); setReason(''); setAction(''); setRefs([]); setConfirmed(false); setError('') }
  const openedTarget = useRef('')
  useEffect(() => {
    if (!open) { openedTarget.current = ''; return }
    if (!inicial || openedTarget.current === inicial) return
    const found = query.data?.find(p => p.id === inicial || p.chave === inicial)
    if (found) { openedTarget.current = inicial; choose(found) }
  }, [open, inicial, query.data])
  async function save() {
    setBusy(true); setError('')
    try {
      const data = { justificativa: reason, ...(adding ? { operacao: 'abrir', objeto_id: object, campo: field, pergunta: question } : { operacao: 'resolver', pendencia_id: selected?.id, assinatura: selected?.assinatura, versao_esperada: selected?.versao, acao: action, revisoes_ids: refs, evidencias_ids: evidenceIds, confirmei_revisao: confirmed }) }
      const hash = JSON.stringify(data)
      retry.current = retry.current?.hash === hash ? retry.current : { hash, id: crypto.randomUUID() }
      await api.post(`/atendimentos/${id}/pendencias-ficha/`, { ...data, client_id: retry.current.id })
      retry.current = null
      setSelected(null); setAdding(false)
      await cache.invalidateQueries({ queryKey: ['pendencias-ficha', id] })
      await cache.invalidateQueries({ queryKey: ['conferencia-atendimento'] })
      await Promise.all(['comparacao-fontes', 'minuta-atendimento', 'ficha-detalhada'].map(key => cache.invalidateQueries({ queryKey: [key] })))
    } catch (err) { const data = (err as { response?: { data?: unknown } }).response?.data; setError(typeof data === 'object' ? JSON.stringify(data) : 'Não foi possível salvar. Atualize e confira a pendência antes de tentar novamente.') }
    finally { setBusy(false) }
  }
  const objects = sheet.data?.objetos || []
  return <Dialog open={open} onClose={() => !busy && onClose()} fullWidth maxWidth="md"><DialogTitle>Pendências por registro</DialogTitle><DialogContent><Stack spacing={2}>
    <Alert severity="info">Conferência local, sem IA real. Só a escrevente decide. Trecho literal não comprova interpretação, identidade ou autenticidade.</Alert>
    <Button onClick={() => { setComparing(!comparing); setSelected(null); setAdding(false) }}>{comparing ? 'Voltar às pendências' : 'Comparar fontes por registro'}</Button>
    {comparing && <ComparacaoFontes id={id} scope={scope} objetos={objects} onReview={async key => { const fresh = await query.refetch(); const p = fresh.data?.find(p => p.chave === key); if (p) choose(p) }} />}
    {(query.isError || sheet.isError) && <Alert severity="error">Falha ao consultar. Reabra este painel antes de decidir.</Alert>}
    <Button onClick={() => { setAdding(true); setComparing(false); setSelected(null); setReason(''); setError('') }}>Registrar dúvida sobre um dado</Button>
    {adding && <>
      <TextField select label="Registro" value={object} onChange={e => { setObject(e.target.value); setField('') }}>{objects.map(o => <MenuItem key={o.id} value={o.id} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere', maxWidth: 'calc(100vw - 48px)' }}>{o.rotulo || `${o.tipo} · ${o.id.slice(0, 8)}`}</MenuItem>)}</TextField>
      <TextField select label="Campo" value={field} onChange={e => setField(e.target.value)}>{objects.find(o => o.id === object)?.campos.map(c => <MenuItem key={c.chave} value={c.chave}>{c.rotulo}</MenuItem>)}</TextField>
      <TextField label="Qual é a dúvida?" multiline value={question} onChange={e => setQuestion(e.target.value)} />
    </>}
    {!comparing && !adding && !selected && query.data?.map(p => <Button key={p.id} sx={{ justifyContent: 'flex-start', textAlign: 'left' }} onClick={() => choose(p)}>{p.situacao} · {p.titulo} {p.objeto_id ? `· ${objects.find(o => o.id === p.objeto_id)?.rotulo || p.objeto_id.slice(0, 8)}` : ''}</Button>)}
    {selected && <>
      <Typography fontWeight={600}>{selected.titulo} · {selected.situacao} · versão {selected.versao}</Typography><Typography>{selected.pergunta}</Typography>
      {selected.objeto_id && <Typography>{objects.find(o => o.id === selected.objeto_id)?.rotulo || `Registro ${selected.objeto_id.slice(0, 8)}`} · campo {selected.campo || 'associação'}</Typography>}
      {selected.tipo !== 'comparacao_fontes' && <FontePendencia issue={selected} />}
      {selected.tipo === 'comparacao_fontes' && <><FontesLadoALado evidencias={selected.contexto.evidencias as EvidenciaComparada[]} />
        <Typography>Marque todas as evidências consideradas, inclusive aquelas que não escolheu. Corrija o valor na ficha antes de decidir, se necessário. Esta decisão não confirma nem rejeita propostas individualmente; confira também as demais pendências.</Typography>
        {(selected.contexto.evidencias as EvidenciaComparada[]).map(e => <FormControlLabel key={e.id} control={<Checkbox checked={evidenceIds.includes(e.id)} onChange={(_, checked) => { setEvidenceIds(checked ? [...evidenceIds, e.id] : evidenceIds.filter(id => id !== e.id)); setConfirmed(false) }} />} label={`${e.tipo_fonte}: ${e.valor_considerado || '(sem dado)'}`} />)}</>}
      {selected.situacao !== 'resolvida' && !selected.acoes.length && <Button onClick={() => { onClose(); document.getElementById('abrir-ficha-detalhada')?.click() }}>Revisar este registro e campo na ficha</Button>}
      {selected.situacao !== 'resolvida' && selected.acoes.length > 0 && <>
        <TextField select label="Decisão" value={action} onChange={e => { setAction(e.target.value); setRefs([]); setConfirmed(false) }}>{selected.acoes.map(a => <MenuItem key={a} value={a}>{a === 'vincular' ? 'Vincular revisões confirmadas' : selected.tipo === 'comparacao_fontes' ? 'Manter campo opcional ausente e sem uso, com motivo' : 'Não utilizar esta fonte, com motivo'}</MenuItem>)}</TextField>
        {action === 'vincular' && objects.filter(o => selected.tipo !== 'comparacao_fontes' || o.id === selected.objeto_id).flatMap(o => o.campos.filter(c => c.atual?.confirmacao_atual && (selected.tipo !== 'comparacao_fontes' || c.chave === selected.campo)).map(c => <FormControlLabel key={c.atual!.id} control={<Checkbox checked={refs.includes(c.atual!.id)} onChange={(_, checked) => { setRefs(checked ? [...refs, c.atual!.id] : refs.filter(r => r !== c.atual!.id)); setConfirmed(false) }} />} label={`${o.rotulo || o.tipo+' '+o.id.slice(0,8)} · ${c.rotulo}: ${c.atual!.valor}`} />))}
        <FormControlLabel control={<Checkbox checked={confirmed} onChange={(_, v) => setConfirmed(v)} />} label="Conferi a dúvida inteira, as fontes e o destino dos dados. Esta decisão não confirma outros campos." />
      </>}
      <Box component="details"><Box component="summary">Histórico ({selected.historico.length})</Box>{selected.historico.map(h => <Box key={h.versao} sx={{ my: 1 }}><Typography>v{h.versao} · {h.situacao} · {h.autor} · {h.data} — {h.motivo}</Typography>{h.resolucao?.campo_opcional_sem_uso && <Typography>Decisão da escrevente: manter o campo opcional ausente e sem uso. Isso não declara inexistência do fato.</Typography>}{h.resolucao?.valor_escolhido && <Typography>Valor escolhido pela escrevente: {h.resolucao.valor_escolhido}</Typography>}{h.resolucao?.evidencias_consideradas && <Box component="details"><Box component="summary">Evidências consideradas na decisão</Box><FontesLadoALado evidencias={h.resolucao.evidencias_consideradas} /></Box>}</Box>)}</Box>
    </>}
    {(adding || selected && selected.acoes.length > 0 && selected.situacao !== 'resolvida') && <><TextField label="Motivo da decisão" multiline value={reason} onChange={e => setReason(e.target.value)} /><Button variant="contained" disabled={busy || !reason.trim() || (adding ? !object || !field || !question.trim() : !action || !confirmed || selected?.tipo === 'comparacao_fontes' && (refs.length !== (action === 'vincular' ? 1 : 0) || evidenceIds.length !== (selected.contexto.evidencias as EvidenciaComparada[]).length))} onClick={save}>Registrar decisão</Button></>}
    {error && <Alert severity="error">{error}</Alert>}
  </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => { setSelected(null); setAdding(false) }}>Lista de pendências</Button><Button disabled={busy} onClick={onClose}>Voltar à conversa</Button></DialogActions></Dialog>
}

function FontePendencia({ issue }: { issue: Issue }) {
  const context = issue.contexto
  const revision = context.revisao as { valor?: string; valor_original?: string; origem?: { trecho?: string; arquivo?: string; pagina?: number; leitura_versao?: number; canal?: string } } | undefined
  const proposal = context.proposta as { trecho?: string; origem?: { arquivo?: string; pagina?: number; leitura_versao?: number; canal?: string } } | undefined
  const source = revision?.origem || proposal?.origem
  const text = String(context.trecho || proposal?.trecho || revision?.origem?.trecho || context.texto || '')
  return <Box component="details"><Box component="summary">Fonte e contexto preservados</Box><Stack spacing={1} sx={{ pt: 1 }}>
    <Typography variant="body2">{String(context.arquivo || source?.arquivo || 'Fonte registrada na ficha e no histórico')} {context.numero || source?.pagina ? `· página ${context.numero || source?.pagina}` : ''} {context.leitura_versao || source?.leitura_versao ? `· leitura ${context.leitura_versao || source?.leitura_versao}` : ''}</Typography>
    {context.linha != null && <Typography variant="body2">Mensagem · linha {String(context.linha)}</Typography>}
    {revision?.valor_original && <Typography sx={{ whiteSpace: 'pre-wrap' }}>Original: {revision.valor_original}</Typography>}
    {revision?.valor && <Typography sx={{ whiteSpace: 'pre-wrap' }}>Valor registrado: {revision.valor}</Typography>}
    {text && <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{text}</Typography>}
    {Boolean(context.texto_ocr) && <><Typography variant="caption">Leitura OCR não confirmada:</Typography><Typography sx={{ whiteSpace: 'pre-wrap' }}>{String(context.texto_ocr)}</Typography></>}
    {Boolean(context.aviso) && <Alert severity="warning">{String(context.aviso)}</Alert>}
    <Typography variant="body2">Para conferir a página original ou a mensagem completa e as decisões associadas, abra a fonte pela ficha detalhada ou pela aba Documentos. Este trecho sozinho não garante interpretação correta.</Typography>
  </Stack></Box>
}
