'use client'

import { useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { ArrowRight, FileText, Paperclip, UploadCloud, X } from 'lucide-react'
import { atendimentosApi } from '@/lib/atendimentos'

export function NovoAtendimento({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter()
  const cache = useQueryClient()
  const [nome, setNome] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [nota, setNota] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState('')
  const [creationUncertain, setCreationUncertain] = useState(false)
  const [createdId, setCreatedId] = useState<string | null>(null)
  const uploaded = useRef(new Set<string>())
  const messageId = useRef<string | null>(null)
  const input = useRef<HTMLInputElement>(null)
  const fileKey = (file: File) => `${file.name}:${file.size}:${file.lastModified}`

  function select(incoming: FileList | null) {
    if (!incoming) return
    setError('')
    const valid: File[] = []
    const existing = new Set(files.map(fileKey))
    for (const file of Array.from(incoming)) {
      if (!/\.(pdf|txt|png|jpe?g)$/i.test(file.name) || file.size > 10 * 1024 * 1024 || !file.size) {
        setError('Use PDF, TXT, PNG ou JPG, com até 10 MB por arquivo. Arquivos vazios não são aceitos.'); continue
      }
      if (!existing.has(fileKey(file))) { valid.push(file); existing.add(fileKey(file)) }
    }
    if (files.length + valid.length > 20) { setError('Adicione até 20 arquivos por vez. Você pode anexar outros no chat.'); return }
    setFiles(old => [...old, ...valid])
  }
  async function start(event: React.FormEvent) {
    event.preventDefault()
    if (!nome.trim() || busy || creationUncertain) return
    setBusy(true); setError('')
    let caseId = createdId
    try {
      if (!caseId) {
        setProgress('Abrindo atendimento…')
        // Do not retry an ambiguous creation automatically: it may already exist.
        try { const item = await atendimentosApi.create(nome.trim()); caseId = item.id; setCreatedId(item.id); void cache.invalidateQueries({ queryKey: ['atendimentos'] }) }
        catch { setCreationUncertain(true); setError('Não foi possível confirmar a criação. Feche esta janela e confira a lista antes de tentar novamente.'); await cache.invalidateQueries({ queryKey: ['atendimentos'] }); return }
      }
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        if (uploaded.current.has(fileKey(file))) continue
        setProgress(`Recebendo documento ${i + 1} de ${files.length}…`)
        await atendimentosApi.upload(caseId, file)
        uploaded.current.add(fileKey(file))
      }
      if (nota.trim()) {
        setProgress('Salvando sua orientação…')
        messageId.current ||= crypto.randomUUID()
        await atendimentosApi.send(caseId, nota.trim(), messageId.current)
      }
      await Promise.all(['atendimentos', 'anexos-atendimento', 'mensagens-atendimento', 'conferencia-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      router.push(`/atendimentos/${caseId}`)
      onClose()
    } catch {
      setError('O atendimento foi salvo, mas o envio não terminou. Tente continuar para reenviar os arquivos pendentes, ou abra a conversa com o que já foi recebido.')
    } finally { setBusy(false); setProgress('') }
  }
  function close() {
    if (busy) return
    onClose()
    setNome(''); setFiles([]); setNota(''); setError(''); setCreatedId(null); setCreationUncertain(false)
    uploaded.current.clear(); messageId.current = null
  }
  return <Dialog open={open} onClose={close} fullWidth maxWidth="sm" aria-labelledby="novo-atendimento-title">
    <Box component="form" onSubmit={start}>
      <DialogTitle id="novo-atendimento-title" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>Vamos começar?<IconButton aria-label="Fechar" disabled={busy} onClick={close}><X size={20} /></IconButton></DialogTitle>
      <DialogContent><Stack spacing={2.5} sx={{ pt: 1 }}>
        <Typography color="text.secondary" fontSize={14}>Dê um nome ao caso, escolha o serviço e reúna os documentos. O próximo passo é a conversa.</Typography>
        <TextField autoFocus label="Como vamos chamar este atendimento?" placeholder="Ex.: Venda do apartamento Centro" required fullWidth value={nome} onChange={e => setNome(e.target.value)} disabled={busy || !!createdId} slotProps={{ htmlInput: { maxLength: 160 } }} />
        <TextField select label="O que você quer preparar?" value="compra_venda" fullWidth disabled={busy || !!createdId}><MenuItem value="compra_venda">Escritura de compra e venda</MenuItem></TextField>
        <Box sx={{ p: 2.5, textAlign: 'center', bgcolor: '#f6f8f1', border: '1px dashed #b8c7ac', borderRadius: '14px' }}>
          <UploadCloud size={26} color="#6e8660" style={{ margin: '0 auto 10px' }} />
          <Typography fontSize={14} fontWeight={600}>Os documentos entram juntos</Typography>
          <Typography fontSize={12} color="text.secondary" sx={{ mt: .5, mb: 1.5 }}>PDF, fotos ou texto · até 10 MB por arquivo</Typography>
          <Button startIcon={<Paperclip size={16} />} variant="outlined" disabled={busy || !!createdId} onClick={() => input.current?.click()}>Selecionar documentos</Button>
          <input ref={input} hidden type="file" multiple accept=".pdf,.txt,.png,.jpg,.jpeg" onChange={e => { select(e.target.files); e.target.value = '' }} />
        </Box>
        {!!files.length && <Stack gap={1}>{files.map(file => <Stack direction="row" alignItems="center" gap={1} key={fileKey(file)}><FileText size={16} /><Typography fontSize={12} sx={{ flex: 1, overflowWrap: 'anywhere' }}>{file.name}</Typography>{uploaded.current.has(fileKey(file)) ? <Chip size="small" label="Recebido" /> : <IconButton aria-label={`Remover ${file.name}`} size="small" disabled={busy || !!createdId} onClick={() => setFiles(old => old.filter(f => fileKey(f) !== fileKey(file)))}><X size={14} /></IconButton>}</Stack>)}</Stack>}
        <TextField label="Quer acrescentar alguma orientação?" placeholder="Opcional. Conte o que precisamos conferir neste caso." multiline minRows={2} fullWidth value={nota} onChange={e => setNota(e.target.value)} disabled={busy || !!createdId} slotProps={{ htmlInput: { maxLength: 10000 } }} />
        <Typography color="text.secondary" fontSize={12}>Leitura local disponível. A análise por IA ainda não está ativada. Nada será confirmado automaticamente.</Typography>
        {busy && <Stack direction="row" gap={1} alignItems="center" role="status"><CircularProgress size={16} /><Typography fontSize={13}>{progress}</Typography></Stack>}
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent>
      <DialogActions><Button disabled={busy} onClick={close}>Cancelar</Button>{createdId && error && <Button disabled={busy} onClick={() => { router.push(`/atendimentos/${createdId}`); onClose() }}>Abrir conversa salva</Button>}<Button type="submit" variant="contained" endIcon={<ArrowRight size={16} />} disabled={busy || creationUncertain || !nome.trim()}>{busy ? 'Preparando…' : createdId ? 'Continuar envio' : 'Continuar para a conversa'}</Button></DialogActions>
    </Box>
  </Dialog>
}
