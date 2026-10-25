'use client'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type MinutaPreparada } from '@/lib/atendimentos'

export function RevisaoFinalDaMinuta({ id, minuta, disabled }: { id: string; minuta: MinutaPreparada; disabled: boolean }) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const [checks, setChecks] = useState([false,false,false])
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const review = minuta.revisao_final
  async function save() {
    if (busy || !checks.every(Boolean) || !reason.trim()) return
    setBusy(true); setError('')
    try {
      await atendimentosApi.revisarMinuta(id, minuta.id, minuta.versao, reason.trim())
      await Promise.all([cache.invalidateQueries({ queryKey: ['minuta-atendimento'] }),cache.invalidateQueries({ queryKey: ['resumo-revisao'] })])
      setOpen(false)
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Não consegui confirmar o registro. Confira se esta versão continua atual antes de tentar novamente.')
      void cache.invalidateQueries({ queryKey: ['minuta-atendimento'] })
    } finally { setBusy(false) }
  }
  return <Stack spacing={1}>
    {review ? <Alert severity={review.texto_corresponde ? 'info' : 'error'}>
      Revisão final desta versão registrada por {review.autor_nome} em {new Date(review.created_at).toLocaleString('pt-BR')}.
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{review.motivo}</Typography>
      {!review.texto_corresponde && <Typography>O texto não corresponde ao registro de revisão. Exportação bloqueada.</Typography>}
    </Alert> : <>
      <Typography variant="body2">Antes de baixar, confira integralmente o texto salvo desta versão e registre a revisão final. Edições posteriores exigem nova revisão.</Typography>
      <Button variant="outlined" disabled={disabled} onClick={() => { setChecks([false,false,false]); setReason(''); setError(''); setOpen(true) }}>Registrar revisão final da v{minuta.versao}</Button>
    </>}
    <Dialog open={open} onClose={() => !busy && setOpen(false)} fullWidth maxWidth="sm"><DialogTitle>Revisão final da minuta v{minuta.versao}</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="info">Este registro documenta sua conferência desta versão. Não assina ou conclui o ato, nem substitui as verificações profissionais aplicáveis. Volte à minuta se ainda precisar conferir algo.</Alert>
        {['Li integralmente o texto salvo, incluindo as alterações manuais.', 'Conferi os dados, valores e condições com os registros do atendimento.', 'Conferi os documentos de origem e os trechos utilizados.'].map((label,index) => <FormControlLabel key={label} control={<Checkbox checked={checks[index]} disabled={busy} onChange={e => setChecks(checks.map((value,i) => i === index ? e.target.checked : value))} />} label={label} />)}
        <TextField label="Observação ou motivo da revisão final" multiline minRows={2} value={reason} disabled={busy} onChange={e => setReason(e.target.value)} slotProps={{ htmlInput: { maxLength: 2000 } }} />
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Voltar sem registrar</Button><Button variant="contained" disabled={busy || !checks.every(Boolean) || !reason.trim()} onClick={save}>{busy ? 'Registrando…' : 'Registrar conferência desta versão'}</Button></DialogActions>
    </Dialog>
  </Stack>
}
