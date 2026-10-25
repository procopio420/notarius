'use client'
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { api } from '@/lib/api'
import { type RegistroFicha } from '@/lib/fichaDetalhada'

export interface EvidenciaComparada {
  id: string; tipo_fonte: string; situacao?: string; valor_original: string; valor_considerado: string; comparavel: boolean; problemas: string[]
  normalizacao: { apresentacao: string }; fonte: { tipo?: string; arquivo?: string; pagina?: number; leitura_versao?: number; organizacao_versao?: number; mensagem_id?: string; canal?: string; trecho?: string }
}
interface Grupo { chave: string; objeto_id: string; campo: string; rotulo: string; problemas: string[]; evidencias: EvidenciaComparada[]; conferencia_necessaria: boolean }
interface SemVinculo { id: string; rotulo: string; valor_original: string; fonte: EvidenciaComparada['fonte']; destinos: { tipo: string; chave: string; rotulo: string }[]; versao_decisao: number; fonte_atual: boolean; objeto_id?: string; campo?: string }
const labels: Record<string, string> = { ausente: 'Dado ausente no registro', formato_invalido: 'Formato ou dígitos inconsistentes', leitura_incerta: 'Leitura incerta ou substituída', vinculo_incerto: 'Vínculo incerto', divergencia: 'Valores divergentes' }
const statusLabels: Record<string, string> = { confirmado: 'Confirmado pela escrevente', informado: 'Informado, sem confirmação', extraido: 'Extraído para revisão', ausente: 'Ausente no registro; não prova inexistência', divergente: 'Marcado como divergente pela escrevente', ilegivel: 'Leitura ilegível', proposta_associada: 'Proposta vinculada, ainda sujeita à conferência', fonte_associada_pela_escrevente: 'Fonte vinculada pela escrevente' }

export function FontesLadoALado({ evidencias }: { evidencias: EvidenciaComparada[] }) {
  return <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' }, gap: 2 }}>{evidencias.map(e => <Box key={e.id} sx={{ border: '1px solid #dce4ee', borderRadius: 2, p: 2, overflowWrap: 'anywhere' }}>
    <Typography fontWeight={600}>{e.tipo_fonte === 'ficha' ? 'Ficha — valor registrado' : e.tipo_fonte === 'documento' ? 'Documento' : 'Mensagem'}</Typography>
    <Typography variant="caption">{statusLabels[e.situacao || ''] || 'Situação preservada no histórico'}</Typography>
    <Typography sx={{ whiteSpace: 'pre-wrap' }}>Original: {e.valor_original || '(não registrado)'}</Typography>
    <Typography sx={{ whiteSpace: 'pre-wrap' }}>Valor considerado: {e.valor_considerado || '(não registrado)'}</Typography>
    <Typography variant="body2">Somente para comparar: {e.normalizacao.apresentacao}</Typography>
    <Typography variant="body2">{e.fonte.arquivo || (e.fonte.mensagem_id ? `Mensagem ${e.fonte.mensagem_id}` : 'Registro da ficha')}{e.fonte.pagina ? ` · página ${e.fonte.pagina} · leitura ${e.fonte.leitura_versao}` : ''}{e.fonte.canal ? ` · ${e.fonte.canal}` : ''}</Typography>
    {e.fonte.trecho && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 1 }}>Trecho literal: {e.fonte.trecho}</Typography>}
    {!!e.problemas.length && <Alert severity="warning">{e.problemas.map(p => labels[p] || p).join('; ')}. {!e.comparavel && 'Não usado como valor comparável.'}</Alert>}
  </Box>)}</Box>
}

export function ComparacaoFontes({ id, scope, objetos, onReview }: { id: string; scope: (string | undefined)[]; objetos: RegistroFicha[]; onReview: (chave: string) => void }) {
  const cache = useQueryClient()
  const query = useQuery({ queryKey: ['comparacao-fontes', id, ...scope], queryFn: async (): Promise<{ grupos: Grupo[]; sem_vinculo: SemVinculo[]; vinculadas: SemVinculo[] }> => (await api.get(`/atendimentos/${id}/comparacao-fontes/`)).data })
  const [selected, setSelected] = useState<SemVinculo | null>(null), [object, setObject] = useState(''), [field, setField] = useState('')
  const [reason, setReason] = useState(''), [checked, setChecked] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const retry = useRef<{ hash: string; id: string } | null>(null)
  async function associate() {
    if (!selected) return
    setBusy(true); setError('')
    const data = { operacao: 'associar', proposta_id: selected.id, versao_esperada: selected.versao_decisao,
      objeto_id: object, campo: field, organizacao_versao: selected.fonte.organizacao_versao,
      justificativa: reason, conferir_associacao: checked }
    const hash = JSON.stringify(data); retry.current = retry.current?.hash === hash ? retry.current : { hash, id: crypto.randomUUID() }
    try {
      await api.post(`/atendimentos/${id}/propostas-dados/`, { ...data, client_id: retry.current.id })
      retry.current = null; setSelected(null)
      await Promise.all(['comparacao-fontes', 'pendencias-ficha', 'propostas-dados', 'ficha-detalhada', 'conferencia-atendimento', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
    } catch { setError('Não foi possível vincular. Confira a classificação do documento, o registro, o campo e as versões; reabra antes de tentar novamente.') }
    finally { setBusy(false) }
  }
  return <Stack spacing={2}>
    <Alert severity="info">Compare apenas registros identificados pela escrevente. A representação normalizada não altera o original nem comprova identidade. Nenhuma fonte tem preferência automática.</Alert>
    {query.isLoading && <Typography>Carregando fontes…</Typography>}
    {query.isError && <Alert severity="error">Não foi possível consultar a comparação.</Alert>}
    {!!query.data?.vinculadas.length && <Box component="details"><Box component="summary">Rever vínculos de propostas já identificadas</Box>{query.data.vinculadas.map(p => <Box key={p.id}><Typography>{p.rotulo} · {p.objeto_id?.slice(0, 8)} · {p.campo} · {p.valor_original}</Typography><Button disabled={!p.fonte_atual || busy} onClick={() => { setSelected(p); setObject(''); setField(''); setReason(''); setChecked(false); setError('') }}>Corrigir vínculo com justificativa</Button></Box>)}</Box>}
    {query.data?.sem_vinculo.map(p => <Box key={p.id} sx={{ border: '1px solid #ddd', p: 2 }}>
      <Typography fontWeight={600}>Vínculo incerto · {p.rotulo}</Typography><Typography sx={{ whiteSpace: 'pre-wrap' }}>{p.valor_original}</Typography>
      <Typography variant="body2">{p.fonte.arquivo || `Mensagem ${p.fonte.mensagem_id}`} · {p.fonte.trecho}</Typography>
      <Button disabled={busy || !p.fonte_atual} onClick={() => { setSelected(p); setObject(''); setField(''); setReason(''); setChecked(false); setError('') }}>Identificar registro e campo para comparar</Button>
      {!p.fonte_atual && <Alert severity="warning">Fonte substituída ou desconsiderada: revise na ficha ou registre a rejeição da proposta com motivo.</Alert>}
    </Box>)}
    {selected && <Stack spacing={2} sx={{ p: 2, border: '1px solid #dce4ee' }}>
      <Typography>Vincular a proposta não confirma seu valor nem altera a ficha.</Typography>
      <TextField select label="Registro identificado" value={object} onChange={e => { setObject(e.target.value); setField(''); setChecked(false) }}>{objetos.filter(o => selected.destinos.some(d => d.tipo === o.tipo)).map(o => <MenuItem key={o.id} value={o.id} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere', maxWidth: 'calc(100vw - 48px)' }}>{o.rotulo || `${o.tipo} · ${o.id.slice(0, 8)}`}</MenuItem>)}</TextField>
      <TextField select label="Campo identificado" value={field} onChange={e => { setField(e.target.value); setChecked(false) }}>{selected.destinos.filter(d => d.tipo === objetos.find(o => o.id === object)?.tipo).map(d => <MenuItem key={d.chave} value={d.chave}>{d.rotulo}</MenuItem>)}</TextField>
      <TextField label="Justificativa do vínculo" multiline value={reason} onChange={e => { setReason(e.target.value); setChecked(false) }} />
      <FormControlLabel control={<Checkbox checked={checked} onChange={(_, v) => setChecked(v)} />} label="Conferi a fonte, a pessoa ou imóvel e o campo. Nome semelhante não comprova vínculo." />
      <Button disabled={busy || !checked || !reason.trim() || !object || !field} onClick={associate}>Registrar vínculo sem confirmar o dado</Button>
      <Button onClick={() => setSelected(null)}>Cancelar vínculo</Button>
    </Stack>}
    {query.data?.grupos.map(g => <Box key={g.chave} sx={{ p: 2, border: '1px solid #dce4ee', borderRadius: 2 }}>
      <Typography fontWeight={600}>{g.rotulo} · {objetos.find(o => o.id === g.objeto_id)?.rotulo || `Registro ${g.objeto_id.slice(0, 8)}`}</Typography>
      <Typography>{g.problemas.length ? g.problemas.map(p => labels[p] || p).join('; ') : 'Sem diferença detectada entre valores comparáveis'}</Typography>
      <FontesLadoALado evidencias={g.evidencias} />
      {g.conferencia_necessaria && <Button onClick={() => onReview(g.chave)}>Ver conferência e registrar decisão</Button>}
    </Box>)}
    {error && <Alert severity="error">{error}</Alert>}
  </Stack>
}
