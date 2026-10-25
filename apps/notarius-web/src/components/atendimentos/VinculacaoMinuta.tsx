'use client'
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { api } from '@/lib/api'
import { fichaDetalhadaApi } from '@/lib/fichaDetalhada'
import type { PosicaoMinuta } from '@/lib/atendimentos'
interface Binding { modelo_aprovado: boolean; modelo_id: string | null; posicoes: PosicaoMinuta[]; versao: number; escopo_assinatura: string; registros: Record<string, string>; exclusoes: { objeto_id: string; motivo: string }[]; atual: boolean; motivo_bloqueio: string; historico: { id: string; versao: number; autor: string; motivo: string; data: string }[] }

export function VinculacaoMinuta({ id, scope }: { id: string; scope: (string | undefined)[] }) {
  const [open, setOpen] = useState(false), [form, setForm] = useState<Binding | null>(null)
  const [registers, setRegisters] = useState<Record<string, string>>({}), [exclusions, setExclusions] = useState<Record<string, string>>({})
  const [reason, setReason] = useState(''), [checked, setChecked] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const retry = useRef<{ hash: string; id: string } | null>(null)
  const cache = useQueryClient()
  const query = useQuery({ queryKey: ['vinculacao-minuta', ...scope], queryFn: async (): Promise<Binding> => (await api.get(`/atendimentos/${id}/vinculacao-minuta/`)).data })
  const sheet = useQuery({ queryKey: ['ficha-vinculacao', ...scope], enabled: open, queryFn: () => fichaDetalhadaApi.get(id) })
  function start() { if (!query.data) return; setForm(query.data); setRegisters(Object.fromEntries(query.data.posicoes.filter(p => query.data.registros[p.chave]).map(p => [p.chave, query.data.registros[p.chave]]))); setExclusions(Object.fromEntries(query.data.exclusoes.map(e => [e.objeto_id, e.motivo]))); setReason(''); setChecked(false); setError(''); setOpen(true) }
  const objects = (sheet.data?.objetos || []).filter(o => !o.campos.some(c => c.chave === 'estado_registro' && c.atual?.valor === 'inativo' && c.atual.confirmacao_atual))
  const complete = !!form?.posicoes.length && form.posicoes.every(p => !!registers[p.chave])
  const outside = objects.filter(o => !Object.values(registers).includes(o.id))
  async function save() {
    if (!form || busy) return
    setBusy(true); setError('')
    const data = { modelo_id: form.modelo_id, versao_esperada: form.versao, escopo_assinatura: form.escopo_assinatura,
      registros: Object.fromEntries(form.posicoes.map(p => [p.chave, registers[p.chave] || ''])),
      exclusoes: objects.filter(o => !Object.values(registers).includes(o.id)).map(o => ({ objeto_id: o.id, motivo: exclusions[o.id] || '' })), motivo: reason, conferir: checked }
    const hash = JSON.stringify(data); retry.current = retry.current?.hash === hash ? retry.current : { hash, id: crypto.randomUUID() }
    try {
      await api.post(`/atendimentos/${id}/vinculacao-minuta/`, { ...data, client_id: retry.current.id })
      retry.current = null; setOpen(false)
      await Promise.all(['vinculacao-minuta', 'minuta-atendimento', 'conferencia-atendimento', 'resumo-revisao'].map(key => cache.invalidateQueries({ queryKey: [key] })))
    } catch (err) { const data = (err as { response?: { data?: unknown } }).response?.data; setError(typeof data === 'object' ? JSON.stringify(data) : 'Não foi possível salvar. Reabra a vinculação antes de decidir novamente.') }
    finally { setBusy(false) }
  }
  return <>
    <Button variant="outlined" disabled={!query.data} onClick={start}>Vincular ficha ao modelo</Button>
    {query.isError && <Alert severity="error">Não foi possível consultar a vinculação da ficha.</Alert>}
    <Dialog open={open} onClose={() => !busy && setOpen(false)} fullWidth maxWidth="md"><DialogTitle>Quem ocupa cada posição do modelo?</DialogTitle><DialogContent><Stack spacing={2}>
      <Alert severity="info">Escolha pessoas, papéis, relações e imóveis separadamente. O rótulo do modelo não comprova papel, identidade ou associação. Revise os vínculos e dê motivo para cada registro que ficar fora desta minuta.</Alert>
      {form?.motivo_bloqueio && <Alert severity="warning">{form.motivo_bloqueio}</Alert>}
      {sheet.isError && <Alert severity="error">Falha ao consultar a ficha. Feche e reabra antes de salvar.</Alert>}
      {!form?.posicoes.length && <Typography>Configure e aprove as posições e os marcadores em “Revisar modelo”. A vinculação ao modelo antigo por blocos continua bloqueada.</Typography>}
      {form?.posicoes.map(p => <Box key={p.chave}><TextField fullWidth select sx={{ '& .MuiSelect-select': { whiteSpace: 'normal', overflowWrap: 'anywhere', height: 'auto' } }} label={`${p.rotulo} · ${p.tipo}`} value={registers[p.chave] || ''} disabled={busy} onChange={e => { setRegisters({ ...registers, [p.chave]: e.target.value }); setChecked(false) }}>{objects.filter(o => o.tipo === p.tipo).map(o => <MenuItem key={o.id} value={o.id} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere', maxWidth: 'calc(100vw - 48px)' }}>{o.rotulo || `${o.tipo} · ${o.id.slice(0, 8)}` }</MenuItem>)}</TextField>{Object.entries(p.vinculos).map(([link, alias]) => <Typography key={link} variant="caption">{link === 'pessoa_a' ? 'Pessoa vinculada' : link === 'pessoa_b' ? 'Segunda pessoa vinculada' : 'Imóvel vinculado'}: deve corresponder à posição {alias}. </Typography>)}</Box>)}
      {!complete && <Typography variant="body2">Primeiro escolha um registro para cada posição. Depois, se sobrar algum registro, informe por que ficará fora desta minuta.</Typography>}
      {complete && outside.map(o => <TextField key={o.id} label={`Por que ${o.rotulo || o.tipo+' '+o.id.slice(0,8)} ficará fora desta minuta?`} multiline required value={exclusions[o.id] || ''} disabled={busy} onChange={e => { setExclusions({ ...exclusions, [o.id]: e.target.value }); setChecked(false) }} />)}
      <TextField label="Motivo da revisão da vinculação" multiline value={reason} disabled={busy} onChange={e => { setReason(e.target.value); setChecked(false) }} />
      <FormControlLabel control={<Checkbox checked={checked} disabled={busy} onChange={(_, v) => setChecked(v)} />} label="Conferi cada posição, os vínculos entre os registros e os motivos de exclusão. Isso não confirma automaticamente os dados." />
      <Box component="details"><Box component="summary">Histórico de vinculações</Box>{query.data?.historico.map(h => <Typography key={h.id}>v{h.versao} · {h.autor} · {h.data} · {h.motivo}</Typography>)}</Box>
      {error && <Alert severity="error">{error}</Alert>}
    </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Voltar</Button><Button variant="contained" disabled={busy || !checked || !reason.trim() || !complete || !form?.modelo_aprovado || outside.some(o => !exclusions[o.id]?.trim()) || !sheet.isSuccess} onClick={save}>Salvar vinculação revisada</Button></DialogActions></Dialog>
  </>
}
