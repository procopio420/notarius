'use client'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type Atendimento } from '@/lib/atendimentos'

export const situacoesAtendimento: Record<string,string> = { em_andamento: 'Em andamento', aguardando: 'Aguardando informação', pausado: 'Pausado' }
export function OrganizacaoAtendimento({ item, scope }: { item: Atendimento; scope: (string | undefined)[] }) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [state, setState] = useState<Atendimento['situacao']>('em_andamento')
  const [version, setVersion] = useState(1)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const history = useQuery({ queryKey: ['organizacao-atendimento', ...scope], queryFn: () => atendimentosApi.historicoOrganizacao(item.id), enabled: open })
  async function save() {
    if (busy) return
    setBusy(true); setError('')
    try {
      const saved = await atendimentosApi.organizar(item.id, { titulo: title.trim(), situacao: state, motivo: reason.trim(), versao_esperada: version })
      cache.setQueryData(['atendimento', ...scope], saved)
      await Promise.all([cache.invalidateQueries({ queryKey: ['atendimentos'] }),cache.invalidateQueries({ queryKey: ['organizacao-atendimento'] })])
      setOpen(false)
    } catch (err) {
      const status = (err as { response?: { status?: number } }).response?.status
      setError(status === 409 ? 'Outro usuário já alterou a organização. Feche, atualize o atendimento e abra novamente antes de salvar.' : 'Não consegui confirmar o salvamento. Seus campos foram mantidos; confira o atendimento antes de repetir.')
      void cache.invalidateQueries({ queryKey: ['atendimento', ...scope] })
    } finally { setBusy(false) }
  }
  return <>
    <Stack direction="row" gap={1} alignItems="center" flexWrap="wrap">
      <Typography variant="body2">Situação: {situacoesAtendimento[item.situacao]}</Typography>
      <Button onClick={() => { setTitle(item.titulo); setState(item.situacao); setVersion(item.versao_cadastro); setReason(''); setError(''); setOpen(true) }}>Organizar atendimento</Button>
    </Stack>
    <Dialog open={open} onClose={() => !busy && setOpen(false)} fullWidth maxWidth="sm"><DialogTitle>Organizar atendimento</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="info">A situação organiza sua lista. Pausar não exclui dados nem encerra o ato. As confirmações e minutas permanecem iguais. Você pode retomar escolhendo “Em andamento”.</Alert>
        <TextField label="Título do atendimento" value={title} onChange={e => setTitle(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength: 160 } }} />
        <TextField select label="Situação do atendimento" value={state} onChange={e => setState(e.target.value as Atendimento['situacao'])} disabled={busy}>
          {Object.entries(situacoesAtendimento).map(([value,label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
        </TextField>
        <TextField label="Motivo da alteração" multiline minRows={2} value={reason} onChange={e => setReason(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength: 2000 } }} />
        {error && <Alert severity="error">{error}</Alert>}
        <Typography fontWeight={600}>Histórico de organização</Typography>
        {history.isLoading && <Typography>Carregando histórico…</Typography>}
        {history.isError && <Alert severity="error" action={<Button onClick={() => history.refetch()}>Tentar novamente</Button>}>Não consegui carregar o histórico.</Alert>}
        {history.isSuccess && !history.data.historico.length && <Typography>Nenhuma alteração de organização registrada.</Typography>}
        {history.isSuccess && history.data.historico.map(event => <Box key={event.versao} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption">v{event.versao} · {event.autor_nome} · {new Date(event.created_at).toLocaleString('pt-BR')}</Typography>
          {event.titulo_anterior !== event.titulo_novo && <Typography sx={{ overflowWrap: 'anywhere' }}>Título: {event.titulo_anterior} → {event.titulo_novo}</Typography>}
          <Typography>{situacoesAtendimento[event.situacao_anterior]} → {situacoesAtendimento[event.situacao_nova]}</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{event.motivo}</Typography>
        </Box>)}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Voltar</Button><Button variant="contained" onClick={save} disabled={busy || !title.trim() || !reason.trim() || (title.trim() === item.titulo && state === item.situacao)}>{busy ? 'Salvando…' : 'Salvar organização'}</Button></DialogActions>
    </Dialog>
  </>
}
