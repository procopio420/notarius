'use client'
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type FeedbackTeste } from '@/lib/atendimentos'

const etapas: Record<string,string> = { conversa:'Conversa', anexos:'Anexos e leitura', ficha:'Dados e conferência', modelo:'Modelo', minuta:'Minuta e revisão', exportacao:'Word/PDF', outro:'Outra parte' }
const tipos: Record<string,string> = { erro:'Algo deu errado', duvida:'Fiquei com dúvida', sugestao:'Tenho uma sugestão' }
function baixar(id: string, notes: FeedbackTeste[]) {
  const lines = ['FEEDBACK DOS TESTES DO SOFTWARE', `Atendimento: ${id}`, 'Estes relatos não alteram nem confirmam dados do ato.', '']
  notes.forEach(note => lines.push(`Registro: ${note.id}`,`${etapas[note.etapa]} · ${tipos[note.tipo]}`,
    `${note.autor_nome} · ${new Date(note.created_at).toLocaleString('pt-BR')}`, note.descricao,
    `Esperava: ${note.esperado || '(não informado)'}`,
    `Contexto: modelo v${note.contexto.modelo_versao ?? '—'}, minuta v${note.contexto.minuta_versao ?? '—'}, ${note.contexto.pendencias} pendência(s) na consulta.`, ''))
  const url = URL.createObjectURL(new Blob(['\ufeff'+lines.join('\r\n')],{ type:'text/plain;charset=utf-8' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `feedback-teste-${id}.txt`; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url),1000)
}
export function FeedbackDoTeste({ id, scope }: { id: string; scope: (string | undefined)[] }) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const [stage, setStage] = useState('outro')
  const [type, setType] = useState('duvida')
  const [description, setDescription] = useState('')
  const [expected, setExpected] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const retry = useRef<{ payload: string; id: string } | null>(null)
  const key = ['feedbacks-teste', ...scope]
  const query = useQuery({ queryKey: key, queryFn: () => atendimentosApi.feedbacks(id), enabled: open, retry: false })
  async function send() {
    if (busy || !description.trim()) return
    const payload = { etapa:stage, tipo:type, descricao:description.trim(), esperado:expected.trim() }
    const signature = JSON.stringify(payload)
    const clientId = retry.current?.payload === signature ? retry.current.id : crypto.randomUUID()
    retry.current = { payload:signature, id:clientId }
    setBusy(true); setError(''); setSuccess('')
    try {
      const saved = await atendimentosApi.registrarFeedback(id,{ ...payload, client_id:clientId })
      cache.setQueryData<FeedbackTeste[]>(key, old => [saved,...(old || []).filter(item => item.id !== saved.id)])
      setDescription(''); setExpected(''); retry.current = null
      setSuccess('Relato salvo neste atendimento. Os dados e a minuta permanecem iguais.')
      void query.refetch()
    } catch { setError('Não consegui confirmar o salvamento. O texto foi mantido; reenviar o mesmo relato não duplica o registro.') }
    finally { setBusy(false) }
  }
  return <>
    <Button onClick={() => setOpen(true)}>Registrar feedback do teste</Button>
    <Dialog open={open} onClose={() => !busy && setOpen(false)} fullWidth maxWidth="md"><DialogTitle>Feedback do teste</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="info">Descreva a dificuldade sem incluir dados pessoais dos documentos. O relato fica no cartório e não é enviado automaticamente ao suporte ou à IA.</Alert>
        <Typography>Se houver um dado incorreto, corrija-o na ficha ou revise a minuta. Registrar feedback não corrige nem confirma informações do atendimento.</Typography>
        <Stack direction={{ xs:'column', sm:'row' }} gap={2}>
          <TextField select label="Onde aconteceu?" value={stage} onChange={e => setStage(e.target.value)} disabled={busy} fullWidth>{Object.entries(etapas).map(([value,label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</TextField>
          <TextField select label="Tipo de relato" value={type} onChange={e => setType(e.target.value)} disabled={busy} fullWidth>{Object.entries(tipos).map(([value,label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</TextField>
        </Stack>
        <TextField label="O que aconteceu ou ficou confuso?" multiline minRows={3} value={description} onChange={e => setDescription(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength:4000 } }} helperText="Inclua os passos para chegar ao problema. Só será salvo ao clicar em Registrar relato." />
        <TextField label="O que você esperava? (opcional)" multiline minRows={2} value={expected} onChange={e => setExpected(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength:2000 } }} />
        {error && <Alert severity="error">{error}</Alert>}{success && <Alert severity="success">{success}</Alert>}
        <Button variant="contained" disabled={busy || !description.trim()} onClick={send}>{busy ? 'Salvando…' : 'Registrar relato'}</Button>
        <Typography variant="h6">Relatos salvos</Typography>
        {query.isFetching && <Typography>Consultando relatos…</Typography>}
        {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não consegui carregar os relatos. O formulário acima continua disponível.</Alert>}
        {query.isSuccess && !query.data.length && <Typography>Nenhum relato registrado neste atendimento.</Typography>}
        {query.isSuccess && query.data.map(note => <Box key={note.id} sx={{ bgcolor:'action.hover', p:2, borderRadius:1 }}>
          <Typography fontWeight={600}>{etapas[note.etapa]} · {tipos[note.tipo]}</Typography>
          <Typography variant="caption">{note.autor_nome} · {new Date(note.created_at).toLocaleString('pt-BR')}</Typography>
          <Typography sx={{ whiteSpace:'pre-wrap', overflowWrap:'anywhere', my:1 }}>{note.descricao}</Typography>
          {note.esperado && <Typography sx={{ whiteSpace:'pre-wrap', overflowWrap:'anywhere' }}>Esperava: {note.esperado}</Typography>}
          <Typography variant="caption">Contexto no registro: modelo v{note.contexto.modelo_versao ?? '—'} · minuta v{note.contexto.minuta_versao ?? '—'} · {note.contexto.pendencias} pendência(s).</Typography>
        </Box>)}
        <Typography variant="caption">Os relatos preservam a redação original. Para corrigir ou complementar um relato, registre outro indicando qual está complementando.</Typography>
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Voltar ao atendimento</Button><Button disabled={!query.isSuccess || query.isFetching || !query.data?.length} onClick={() => query.data && baixar(id,query.data)}>Baixar relatos TXT</Button></DialogActions>
    </Dialog>
  </>
}
