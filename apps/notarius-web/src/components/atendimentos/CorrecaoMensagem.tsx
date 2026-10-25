'use client'
import { useRef, useState } from 'react'
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from '@mui/material'
import { useQueryClient } from '@tanstack/react-query'
import { atendimentosApi, type Mensagem } from '@/lib/atendimentos'
import { useRascunhoSessao } from '@/lib/rascunhoSessao'

export function CorrecaoMensagem({ id, scope, mensagem, substituida }: { id: string; scope: (string | undefined)[]; mensagem: Mensagem; substituida: boolean }) {
  const cache = useQueryClient()
  const local = useRascunhoSessao(scope, `correcao:${mensagem.id}`, { text: mensagem.texto, reason: '', hash: '', id: '' }, (v): v is { text: string; reason: string; hash: string; id: string } => !!v && ['text', 'reason', 'hash', 'id'].every(k => typeof (v as Record<string, unknown>)[k] === 'string'))
  const [open, setOpen] = useState(false)
  const { text, reason } = local.value
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  const retry = useRef<{ hash: string; id: string } | null>(null)
  async function save() {
    const hash = JSON.stringify([text, reason]); retry.current = retry.current?.hash === hash ? retry.current : { hash, id: crypto.randomUUID() }
    if (local.value.hash === hash && local.value.id) retry.current = { hash, id: local.value.id }
    local.save({ text, reason, ...retry.current })
    setBusy(true); setError('')
    try {
      await atendimentosApi.corrigirMensagem(id, mensagem.id, { texto: text, justificativa: reason, client_id: retry.current.id })
      await Promise.all(['mensagens-atendimento', 'conferencia-atendimento', 'roteiro-conversa', 'ficha-detalhada', 'ficha-atendimento', 'pendencias-ficha', 'comparacao-fontes', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      retry.current = null; local.clear(); setOpen(false)
    } catch { setError('A correção não foi confirmada. Seu texto foi mantido; confira se outra correção já foi registrada antes de reenviar.') }
    finally { setBusy(false) }
  }
  return <><Button disabled={substituida || !local.ready} onClick={() => { setOpen(true); setError('') }}>{substituida ? 'Existe correção posterior no histórico' : local.exists ? 'Retomar correção não enviada' : 'Corrigir esta resposta'}</Button>
    <Dialog open={open} onClose={() => !busy && setOpen(false)} fullWidth maxWidth="sm"><DialogTitle>Corrigir resposta anterior</DialogTitle><DialogContent><Stack spacing={2}>
      <Typography sx={{ whiteSpace: 'pre-wrap' }}>Original preservado: {mensagem.texto}</Typography>
      <Alert severity="info">A correção será uma nova mensagem com sua justificativa. Dados que usavam a mensagem anterior precisarão de revisão; nenhum campo será confirmado ou corrigido automaticamente.</Alert>
      <TextField label="Texto corrigido" multiline minRows={2} value={text} onChange={e => local.save({ ...local.value, text: e.target.value })} slotProps={{ htmlInput: { maxLength: 10000 } }} />
      <TextField label="Motivo da correção" multiline value={reason} onChange={e => local.save({ ...local.value, reason: e.target.value })} />
      {local.aviso && <Alert severity="warning">{local.aviso}</Alert>}
      {error && <Alert severity="error">{error}</Alert>}
    </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Voltar sem enviar</Button><Button disabled={busy || !text.trim() || !reason.trim()} onClick={save}>Registrar correção sem confirmar dados</Button></DialogActions></Dialog></>
}
