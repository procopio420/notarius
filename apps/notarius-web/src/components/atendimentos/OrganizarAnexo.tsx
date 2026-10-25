'use client'
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { api } from '@/lib/api'
import { type Anexo } from '@/lib/atendimentos'
import { type RegistroFicha } from '@/lib/fichaDetalhada'

export const finalidadesDocumento: Record<string, string> = { pendente: 'Finalidade ou vínculo ainda incerto', caso: 'Documento do caso', referencia_redacao: 'Referência de redação — não comprova dados do caso', nao_utilizar: 'Não utilizar neste caso' }
interface Link { objeto_id: string; todas: boolean; paginas: string }
export function nomeDestinatario(obj: RegistroFicha): string { return `${obj.tipo === 'pessoa' ? 'Pessoa' : 'Imóvel'} · ${obj.campos.find(c => c.chave === (obj.tipo === 'pessoa' ? 'nome' : 'descricao'))?.atual?.valor || 'sem identificação registrada'} · ${obj.id.slice(0, 8)}` }
export function OrganizarAnexo({ id, scope, anexo, objetos, onClose }: { id: string; scope: (string | undefined)[]; anexo: Anexo; objetos: RegistroFicha[]; onClose: () => void }) {
  const [openedVersion] = useState(anexo.organizacao.versao), [openedReading] = useState(anexo.leitura_versao)
  const [purpose, setPurpose] = useState(anexo.organizacao.finalidade), [type, setType] = useState(anexo.organizacao.tipo_documento)
  const [links, setLinks] = useState<Link[]>(anexo.organizacao.vinculos.map(v => ({ objeto_id: v.objeto_id || 'atendimento', todas: !v.paginas.length, paginas: v.paginas.join(', ') })))
  const [reason, setReason] = useState(''), [checked, setChecked] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const cache = useQueryClient(), retry = useRef<{ hash: string; id: string } | null>(null)
  const history = useQuery({ queryKey: ['organizacao-anexo', ...scope, anexo.id], queryFn: async (): Promise<{ historico: { id: string; versao: number; finalidade: string; tipo_documento: string; leitura_versao: number; vinculos: { objeto_id: string | null; paginas: number[] }[]; autor: string; data: string; motivo: string }[] }> => (await api.get(`/atendimentos/${id}/anexos/${anexo.id}/organizacao/`)).data })
  function update(index: number, change: Partial<Link>) { setLinks(links.map((v, i) => i === index ? { ...v, ...change } : v)); setChecked(false) }
  function owner(oid: string | null) { return oid ? objetos.find(o => o.id === oid) ? nomeDestinatario(objetos.find(o => o.id === oid)!) : `Registro ${oid}` : 'Atendimento, sem pessoa ou imóvel específico' }
  async function save() {
    setError('')
    const selected = []
    for (const link of purpose === 'caso' ? links : []) {
      if (!link.objeto_id || !link.todas && !/^\s*\d+(?:\s*,\s*\d+)*\s*$/.test(link.paginas)) { setError('Escolha o destinatário e marque todas as páginas ou informe números separados por vírgula.'); return }
      selected.push({ objeto_id: link.objeto_id === 'atendimento' ? null : link.objeto_id, paginas: link.todas ? [] : link.paginas.split(',').map(p => Number(p.trim())) })
    }
    const data = { versao_esperada: openedVersion, leitura_versao: openedReading, finalidade: purpose, tipo_documento: type, vinculos: selected, motivo: reason, conferi: checked }
    const hash = JSON.stringify(data); retry.current = retry.current?.hash === hash ? retry.current : { hash, id: crypto.randomUUID() }
    setBusy(true)
    try {
      await api.post(`/atendimentos/${id}/anexos/${anexo.id}/organizacao/`, { ...data, client_id: retry.current.id })
      retry.current = null
      await Promise.all(['anexos-atendimento', 'organizacao-anexo', 'ficha-detalhada', 'ficha-atendimento', 'propostas-dados', 'conferencia-atendimento', 'pendencias-ficha', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      onClose()
    } catch (err) { const data = (err as { response?: { data?: unknown } }).response?.data; setError(typeof data === 'object' ? JSON.stringify(data) : 'Não foi possível salvar. Reabra a classificação antes de decidir novamente.') }
    finally { setBusy(false) }
  }
  return <Dialog open onClose={() => !busy && onClose()} fullWidth maxWidth="md"><DialogTitle>Organizar documento · {anexo.nome}</DialogTitle><DialogContent><Stack spacing={2}>
    <Alert severity="info">O original será preservado. Escolha tipo, finalidade e destinatários explicitamente. Nome parecido e trecho literal não comprovam identidade ou associação; esta revisão não confirma os campos do documento.</Alert>
    <Typography>Leitura aberta {openedReading} · classificação aberta v{openedVersion}</Typography>
    {(openedVersion !== anexo.organizacao.versao || openedReading !== anexo.leitura_versao) && <Alert severity="warning">O documento foi atualizado enquanto este formulário estava aberto. Volte e reabra a classificação antes de salvar.</Alert>}
    {!anexo.organizacao.leitura_atual && anexo.organizacao.versao > 0 && <Alert severity="warning">A leitura foi substituída. Confira novamente o documento e os vínculos por página.</Alert>}
    <TextField select label="Finalidade deste arquivo" value={purpose} disabled={busy} onChange={e => { setPurpose(e.target.value); setChecked(false) }}>{Object.entries(finalidadesDocumento).map(([v, label]) => <MenuItem key={v} value={v}>{label}</MenuItem>)}</TextField>
    <TextField label="Tipo do documento, conforme sua revisão" value={type} disabled={busy} onChange={e => { setType(e.target.value); setChecked(false) }} helperText="Ex.: identificação, matrícula, procuração, guia, certidão ou outro tipo definido pela escrevente. Nenhum tipo foi deduzido." />
    {purpose === 'referencia_redacao' && <Alert severity="warning">Este arquivo servirá somente para consultar a redação. Dados e resultados do exemplo não poderão alimentar a ficha como comprovação deste caso.</Alert>}
    {purpose === 'caso' && <>
      <Typography fontWeight={600}>A quem pertence e em quais páginas?</Typography>
      {links.map((link, index) => <Box key={index} sx={{ p: 2, border: '1px solid #ddd', borderRadius: 2 }}><Stack spacing={1}>
        <TextField select label="Destinatário explícito" value={link.objeto_id} disabled={busy} onChange={e => update(index, { objeto_id: e.target.value })}><MenuItem value="atendimento">Atendimento, sem pessoa ou imóvel específico</MenuItem>{objetos.filter(o => ['pessoa', 'imovel'].includes(o.tipo)).map(o => <MenuItem key={o.id} value={o.id}>{nomeDestinatario(o)}</MenuItem>)}</TextField>
        <FormControlLabel control={<Checkbox disabled={busy} checked={link.todas} onChange={(_, v) => update(index, { todas: v })} />} label="Este vínculo abrange todas as páginas/unidades deste arquivo" />
        {!link.todas && <TextField label="Páginas deste vínculo (ex.: 1, 2)" value={link.paginas} disabled={busy} onChange={e => update(index, { paginas: e.target.value })} />}
        <Button disabled={busy} onClick={() => { setLinks(links.filter((_, i) => i !== index)); setChecked(false) }}>Retirar este vínculo do rascunho</Button>
      </Stack></Box>)}
      <Button disabled={busy} onClick={() => { setLinks([...links, { objeto_id: '', todas: false, paginas: '' }]); setChecked(false) }}>Adicionar destinatário e páginas</Button>
      <Typography variant="body2">Um PDF pode reunir documentos de várias pessoas ou imóveis. Registre cada vínculo e sua abrangência. A classificação não permite transferir um dado de uma pessoa a outra.</Typography>
    </>}
    <TextField label="Motivo da classificação ou correção" multiline value={reason} disabled={busy} onChange={e => { setReason(e.target.value); setChecked(false) }} />
    <FormControlLabel control={<Checkbox disabled={busy} checked={checked} onChange={(_, v) => setChecked(v)} />} label="Conferi a finalidade, o tipo, os destinatários e as páginas. A decisão não confirma dados nem autentica o documento." />
    <Box component="details"><Box component="summary">Histórico de classificação e vínculos</Box>{history.data?.historico.map(h => <Box key={h.id} sx={{ py: 1 }}><Typography>v{h.versao} · {h.tipo_documento || 'Tipo pendente'} · {finalidadesDocumento[h.finalidade]} · leitura {h.leitura_versao}</Typography><Typography>{h.autor} · {h.data} · {h.motivo}</Typography>{h.vinculos.map((v, i) => <Typography key={i} variant="body2">{owner(v.objeto_id)} · {v.paginas.length ? `páginas ${v.paginas.join(', ')}` : 'todas as páginas/unidades'}</Typography>)}</Box>)}</Box>
    {history.isError && <Alert severity="error">Não foi possível consultar o histórico. Reabra antes de decidir.</Alert>}
    {error && <Alert severity="error">{error}</Alert>}
  </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={onClose}>Voltar</Button><Button variant="contained" disabled={busy || history.isError || !checked || !reason.trim() || purpose === 'caso' && (!type.trim() || !links.length)} onClick={save}>Salvar nova classificação</Button></DialogActions></Dialog>
}
