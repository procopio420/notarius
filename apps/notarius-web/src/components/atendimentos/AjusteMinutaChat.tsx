import { useRef, useState } from 'react'
import { Alert, Box, Button, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type MinutaPreparada, type PerguntaConferencia, type PedidoDocumento } from '@/lib/atendimentos'
import { fonteMencionada, type interpretarPedidoDeAjuste } from '@/lib/ajusteMinuta'

type Candidato = PerguntaConferencia['candidatos'][number]
type Pedido = NonNullable<ReturnType<typeof interpretarPedidoDeAjuste>> & { texto: string }

export function AjusteMinutaChat({ id, minuta, pedido, perguntas, onSaved, onSource, onClose }: {
  id: string; minuta: MinutaPreparada; pedido: Pedido; perguntas: PerguntaConferencia[]
  onSaved: () => Promise<void>; onSource: (source: Omit<PedidoDocumento, 'token' | 'acao'>) => void; onClose: () => void
}) {
  const [selection, setSelection] = useState<{ question: PerguntaConferencia; candidate: Candidato } | null>(null)
  const [confirm, setConfirm] = useState(false)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const retry = useRef<{ content: string; id: string } | null>(null)
  const affected = perguntas.filter(question => !!minuta.dados[question.chave]
    && ((!pedido.campos.length && !pedido.pessoaIndefinida) || pedido.campos.some(key => key === question.chave))
    && question.candidatos.some(candidate => candidate.origem === 'documento'))

  async function save() {
    if (!selection || !confirm || !reason.trim() || busy) return
    const { question, candidate } = selection
    if (!candidate.canal || !candidate.organizacao_versao) return
    const payload = {
      chave: question.chave, assinatura: question.assinatura, versao_esperada: question.versao,
      valor: candidate.valor, confirmar: true, justificativa: reason.trim(),
      fonte_documental: { pagina_id: candidate.id, canal: candidate.canal, trecho: candidate.trecho,
        organizacao_versao: candidate.organizacao_versao },
    }
    const content = JSON.stringify(payload)
    const clientId = retry.current?.content === content ? retry.current.id : crypto.randomUUID()
    retry.current = { content, id: clientId }
    setBusy(true); setError('')
    try {
      await atendimentosApi.responder(id, { ...payload, client_id: clientId })
      setSaved(question.rotulo); setSelection(null)
      await onSaved()
    } catch (err) {
      const status = (err as { response?: { status: number } }).response?.status
      setError(status === 409 ? 'A fonte ou a ficha mudou. Reabra as pendências e confira a versão atual.'
        : 'Não foi possível salvar a decisão. Confira a classificação e a página do documento.')
    } finally { setBusy(false) }
  }

  return <Stack component="section" aria-label="Proposta de ajuste da minuta" spacing={1.25} sx={{ minWidth: 0 }}>
    <Typography component="h2" variant="subtitle1" fontWeight={650}>Proposta de ajuste da minuta</Typography>
    <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{pedido.texto}</Typography>
    {pedido.pessoaIndefinida && <Alert severity="info">Para alterar nome ou grafia, informe se é a parte vendedora ou compradora. Confira o campo completo e o documento correspondente.</Alert>}
    {saved && <Alert severity="success">Decisão registrada em {saved}. Prepare uma nova versão após resolver as pendências. A minuta anterior continua no histórico.</Alert>}
    {!affected.length && !saved && <Typography variant="body2">Não encontrei um campo pendente da minuta com trecho de documento para este pedido. Confira as fontes em Revisão e ajustes.</Typography>}
    {affected.map(question => <Box key={question.chave} sx={{ border: 1, borderColor: 'divider', p: 1.5, borderRadius: 2 }}>
      <Typography variant="subtitle2">{question.rotulo}</Typography>
      <Typography variant="caption">Na minuta v{minuta.versao}</Typography>
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{minuta.dados[question.chave].valor}</Typography>
      {question.tipo === 'divergencia' && <Typography variant="body2" color="warning.dark" sx={{ mt: 1 }}>Há valores divergentes. Escolha uma fonte para revisar.</Typography>}
      {question.candidatos.filter(candidate => candidate.origem === 'documento')
        .map(candidate => ({ candidate, mentioned: fonteMencionada(pedido.texto, candidate.arquivo) }))
        .sort((a, b) => Number(b.mentioned) - Number(a.mentioned)).map(({ candidate, mentioned }, index) => {
        const active = selection?.question.chave === question.chave && selection.candidate.id === candidate.id
          && selection.candidate.trecho === candidate.trecho && selection.candidate.canal === candidate.canal
        const { anexo_id, leitura_versao } = candidate
        return <Stack key={`${candidate.id}:${candidate.canal}:${index}`} spacing={.5} sx={{ mt: 1, p: 1, bgcolor: 'action.hover' }}>
          <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>{candidate.arquivo} · página {candidate.pagina} · leitura v{candidate.leitura_versao}{candidate.canal === 'ocr' ? ' · OCR' : ''}</Typography>
          {mentioned && <Typography variant="caption" fontWeight={650}>Fonte mencionada no pedido</Typography>}
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{candidate.trecho}</Typography>
          <Stack direction="row" gap={.5} flexWrap="wrap">
            {anexo_id && <Button size="small" onClick={() => onSource({ anexo_id, pagina_id: candidate.id, leitura_versao })}>Abrir fonte</Button>}
            <Button size="small" variant={active ? 'contained' : 'outlined'} aria-pressed={active} disabled={busy || !candidate.organizacao_versao} onClick={() => {
              setSelection({ question, candidate }); setConfirm(false); setSaved(''); setError('')
            }}>Propor este valor</Button>
          </Stack>
          {!candidate.organizacao_versao && <Typography variant="caption">Identifique o documento para selecionar esta fonte.</Typography>}
        </Stack>
      })}
    </Box>)}
    {selection && <Stack spacing={1}>
      <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>Na nova versão, <strong>{selection.question.rotulo}</strong> passa a <strong>{selection.candidate.valor}</strong>, com origem em {selection.candidate.arquivo}.</Typography>
      <TextField label="Motivo do ajuste" value={reason} onChange={event => setReason(event.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength: 2000 } }} />
      <FormControlLabel control={<Checkbox checked={confirm} onChange={event => setConfirm(event.target.checked)} disabled={busy} />} label="Conferi o trecho e confirmo esta mudança na ficha." />
      <Button variant="contained" onClick={() => void save()} disabled={busy || !confirm || !reason.trim()} sx={{ alignSelf: 'flex-start' }}>Registrar decisão do ajuste</Button>
    </Stack>}
    {error && <Alert severity="error">{error}</Alert>}
    <Button size="small" disabled={busy} onClick={onClose} sx={{ alignSelf: 'flex-start' }}>Fechar proposta</Button>
  </Stack>
}
