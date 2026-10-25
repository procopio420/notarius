'use client'

import { PendenciasFicha } from './PendenciasFicha'
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Paper, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type PerguntaConferencia, type RespostaConferencia, type PedidoFicha, type PedidoDocumento } from '@/lib/atendimentos'

export function PerguntasConferencia({ id, scope, onReviewMessage, onAttach, onDraft, onStructured }: { id: string; scope: (string | undefined)[]; onReviewMessage?: (id: string) => void; onAttach?: (pedido?: Omit<PedidoDocumento, 'token'>) => void; onDraft?: () => void; onStructured?: (pedido: Omit<PedidoFicha, 'token'>) => void }) {
  const cache = useQueryClient()
  const query = useQuery({ queryKey: ['conferencia-atendimento', ...scope], queryFn: () => atendimentosApi.roteiro(id), refetchOnWindowFocus: true })
  const [question, setQuestion] = useState<PerguntaConferencia | null>(null)
  const [value, setValue] = useState('')
  const [reason, setReason] = useState('')
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [issues, setIssues] = useState(false)
  const [all, setAll] = useState(false)
  const [issueTarget, setIssueTarget] = useState<string | null>(null)
  const retry = useRef<{ signature: string; id: string } | null>(null)
  function open(q: PerguntaConferencia) {
    if (q.tipo === 'organizacao_documento') { setAll(false); onAttach?.({ anexo_id: q.chave.split(':')[1], acao: 'organizacao' }); return }
    if (q.tipo === 'vinculacao_minuta') { setAll(false); onDraft?.(); return }
    if (q.tipo === 'pendencia_ficha') {
      setAll(false)
      const target = q.destino
      if (target?.anexo_id && ['pagina', 'arquivo_sem_leitura'].includes(target.subtipo || '')) {
        onAttach?.({ anexo_id: target.anexo_id, pagina_id: target.pagina_id || undefined, acao: 'leitura' }); return
      }
      if (target?.objeto_id && target.campo && ['ausencia', 'confirmacao', 'leitura', 'dependencia', 'divergencia', 'registro_vazio'].includes(target.subtipo || '') && onStructured) {
        onStructured({ objeto_id: target.objeto_id, campo: target.campo }); return
      }
      setIssueTarget(target?.pendencia_id || q.chave); setIssues(true); return
    }
    if (q.tipo === 'estrutura') { setAll(false); document.getElementById('abrir-ficha-detalhada')?.click(); return }
    if (q.tipo === 'anexar') { setAll(false); if (onAttach) onAttach(); else document.getElementById('anexar-arquivo')?.scrollIntoView({ behavior: 'smooth', block: 'center' }); return }
    setQuestion(q); setValue(q.atual || ''); setReason(''); setConfirm(false); setError(''); setAll(false)
  }
  async function send() {
    if (!question || busy) return
    const payload = { chave: question.chave, assinatura: question.assinatura, versao_esperada: question.versao, valor: value.trim(), confirmar: confirm, justificativa: reason.trim() }
    const signature = JSON.stringify(payload)
    const clientId = retry.current?.signature === signature ? retry.current.id : crypto.randomUUID()
    retry.current = { signature, id: clientId }
    setBusy(true); setError('')
    try {
      await atendimentosApi.responder(id, { ...payload, client_id: clientId } as RespostaConferencia)
      await Promise.all([
        cache.invalidateQueries({ queryKey: ['conferencia-atendimento'] }),
        cache.invalidateQueries({ queryKey: ['mensagens-atendimento'] }),
        cache.invalidateQueries({ queryKey: ['ficha-atendimento'] }),
        cache.invalidateQueries({ queryKey: ['atendimentos'] }),
        cache.invalidateQueries({ queryKey: ['minuta-atendimento'] }),
      ])
      setQuestion(null); retry.current = null
    } catch (err) {
      const status = (err as { response?: { status: number } }).response?.status
      const details = (err as { response?: { data?: unknown } }).response?.data
      setError(status === 409 ? 'As informações mudaram. Feche esta pergunta e abra a versão atualizada antes de responder.' : Array.isArray(details) ? details.join(' ') : 'Não foi possível confirmar o salvamento. Sua resposta foi mantida; tente novamente.')
      if (status === 409) void query.refetch()
    } finally { setBusy(false) }
  }
  const next = query.isError ? undefined : query.data?.proxima
  return <>
    <Button onClick={() => { setIssueTarget(null); setIssues(true) }}>Pendências por registro e histórico</Button>
    <PendenciasFicha key={scope.join(':')} id={id} scope={scope} open={issues} inicial={issueTarget} onClose={() => setIssues(false)} />
    <Paper elevation={0} sx={{ p: 2.5, border: '1px solid #dce4ee', borderRadius: 3, bgcolor: '#f5f9ff' }}>
      <Stack spacing={2}>
        <Typography component="h2" sx={{ fontSize: 20, fontWeight: 650 }}>Próximo passo</Typography>
        <Typography variant="caption">Orientação local por regras, sem IA real. Somente a escrevente confirma os dados.</Typography>
        {query.data?.recebido && <Box><Typography variant="body2">Recebido: {query.data.recebido.mensagens} mensagem(ns), {query.data.recebido.documentos} documento(s), {query.data.recebido.propostas} proposta(s).</Typography><Typography variant="body2">Ficha: {query.data.recebido.pessoas} pessoa(s) e {query.data.recebido.imoveis} imóvel(is). {query.data.total_pendencias} pendência(s) para revisão.</Typography><Typography variant="caption">Recebido não significa interpretado ou confirmado.</Typography></Box>}
        {onStructured && <Button onClick={() => onStructured({ novo_participante: true })}>Acrescentar participante</Button>}
        {query.isLoading && <Typography>Conferindo informações…</Typography>}
        {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não consegui conferir os dados. Atualize antes de continuar.</Alert>}
        {next && <>
          <Typography>{next.tipo === 'anexar' ? 'Envie os documentos deste atendimento para começarmos a conferência.' : next.pergunta}</Typography>
          {next.destino?.trecho && <Alert severity="warning"><Typography variant="body2">Trecho exato que ficou incerto:</Typography><Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{next.destino.trecho}</Typography></Alert>}
          {next.destino?.objeto_id && <Typography variant="caption">{next.destino.registro_rotulo || `Registro ${next.destino.objeto_id.slice(0, 8)}`}{next.destino.campo ? ` · ${next.destino.campo}` : ''}</Typography>}
          <Stack spacing={1}>
            <Button variant="contained" disableElevation onClick={() => next.tipo === 'documento' && onAttach ? onAttach() : open(next)}>{next.tipo === 'organizacao_documento' ? 'Organizar documento' : next.tipo === 'vinculacao_minuta' ? 'Abrir modelo e vinculação na Minuta' : next.tipo === 'estrutura' ? 'Abrir ficha detalhada' : next.tipo === 'anexar' ? 'Enviar documentos' : next.tipo === 'documento' ? 'Abrir documentos' : next.destino?.subtipo === 'pagina' ? 'Conferir página do documento' : next.destino?.subtipo === 'arquivo_sem_leitura' ? 'Conferir arquivo sem leitura' : 'Responder à pergunta'}</Button>
            {next.tipo === 'pendencia_ficha' && ['pagina', 'arquivo_sem_leitura'].includes(next.destino?.subtipo || '') && <Button onClick={() => { setIssueTarget(next.destino?.pendencia_id || next.chave); setIssues(true) }}>Registrar revisão manual desta fonte</Button>}
            {next.tipo === 'documento' && <Button onClick={() => open(next)}>Já conferi: registrar revisão</Button>}
            {(query.data?.pendencias.length || 0) > 1 && <Button onClick={() => setAll(true)}>Ver todas as pendências ({query.data?.pendencias.length})</Button>}
          </Stack>
          <Typography variant="body2" color="text.secondary">A minuta aguarda a conferência das pendências.</Typography>
        </>}
        {query.isSuccess && !next && <>
          <Typography>As verificações iniciais foram respondidas. Vá à aba Minuta para revisar o modelo e preparar o texto.</Typography>
          {onDraft && <Button variant="contained" disableElevation onClick={onDraft}>Ir para minuta</Button>}
        </>}
        {query.isSuccess && !query.isFetching && query.data.orientacao?.nao_interpretados.length > 0 && <Alert severity="warning">
          <Typography variant="body2" fontWeight={600}>Este trecho precisa da sua interpretação:</Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: 180, overflow: 'auto', mt: 1 }}>{query.data.orientacao.nao_interpretados.join('\n')}</Typography>
          {onReviewMessage && query.data.orientacao.mensagem_id && <Button onClick={() => onReviewMessage(query.data.orientacao.mensagem_id!)}>Conferir este trecho</Button>}
        </Alert>}
        {query.isSuccess && !query.isFetching && query.data.orientacao?.identificados.length > 0 && <Box component="details" sx={{ borderTop: '1px solid #dce4ee', pt: 1.5 }}>
          <Box component="summary" sx={{ cursor: 'pointer', color: 'primary.main', fontWeight: 600, py: 1 }}>Informações da última mensagem</Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Propostas para sua revisão, ainda sem confirmação automática.</Typography>
          {query.data.orientacao.identificados.map((field,i) => <Box key={i} sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight={600}>{field.rotulo}</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{field.trecho}</Typography>
            {query.data.pendencias.find(q => q.chave === field.chave) && <Button size="small" onClick={() => open(query.data.pendencias.find(q => q.chave === field.chave)!)}>Conferir informação</Button>}
          </Box>)}
        </Box>}
        {query.isFetching && !query.isLoading && <Typography variant="body2" role="status">Atualizando a conferência…</Typography>}
      </Stack>
    </Paper>
    <Dialog open={all} onClose={() => setAll(false)} fullWidth maxWidth="sm"><DialogTitle>O que falta conferir?</DialogTitle>
      <DialogContent><Stack spacing={1}>{query.data?.pendencias.map(q => <Button key={q.chave} onClick={() => open(q)} sx={{ justifyContent: 'flex-start', textAlign: 'left' }}>{q.rotulo} · {q.tipo === 'divergencia' ? 'informações diferentes' : q.tipo === 'documento' ? 'revisão manual' : 'aguardando resposta'}</Button>)}</Stack></DialogContent>
      <DialogActions><Button onClick={() => setAll(false)}>Voltar à conversa</Button></DialogActions></Dialog>
    <Dialog open={!!question} onClose={() => !busy && setQuestion(null)} fullWidth maxWidth="sm"><DialogTitle sx={{ overflowWrap: 'anywhere' }}>{question?.rotulo}</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Typography>{question?.pergunta}</Typography>
        {question?.tipo === 'mensagem' && <Alert severity="warning"><Typography sx={{ whiteSpace: 'pre-wrap' }}>{question.atual}</Typography><Typography>Trecho não interpretado. Confira pessoas, papéis e condições e registre as decisões nos campos afetados. A revisão não confirma automaticamente nenhum campo.</Typography></Alert>}
        {question?.tipo === 'documento' && <Alert severity="warning">Abra o original em “Baixar original”. Só confirme depois de conferir manualmente e registrar os dados relevantes. Esta ação não significa que o sistema conseguiu ler o arquivo.</Alert>}
        {question?.candidatos.map((c, index) => <Box key={`${c.id}-${index}`} sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
          <Typography variant="caption">{c.origem === 'documento' ? `${c.arquivo} · página ${c.pagina}${c.canal === 'ocr' ? ' · OCR não confirmado' : ''}` : 'Mensagem da conversa'}</Typography>
          <Typography variant="caption" display="block">{c.origem === 'documento' ? `Extraído · leitura ${c.leitura_versao ?? 'não identificada'}` : 'Informado na conversa'} · proposta sem confirmação. Trecho literal não garante interpretação correta.</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{c.trecho}</Typography>
          <Button size="small" disabled={busy} onClick={() => { setValue(c.valor); setConfirm(false) }}>Usar este valor para revisar</Button>
        </Box>)}
        {!['documento', 'mensagem'].includes(question?.tipo || '') && <TextField label="Sua resposta" multiline minRows={2} value={value} onChange={e => { setValue(e.target.value); setConfirm(false) }} disabled={busy} slotProps={{ htmlInput: { maxLength: 10000 } }} />}
        <TextField label={['documento', 'mensagem'].includes(question?.tipo || '') ? 'O que você conferiu manualmente?' : 'Motivo ou fonte da sua decisão'} multiline minRows={2} required value={reason} onChange={e => { setReason(e.target.value); setConfirm(false) }} disabled={busy} slotProps={{ htmlInput: { maxLength: 2000 } }} />
        <FormControlLabel control={<Checkbox checked={confirm} onChange={e => setConfirm(e.target.checked)} disabled={busy} />} label={['documento', 'mensagem'].includes(question?.tipo || '') ? 'Resolvi as dúvidas desta fonte e registrei os dados relevantes nos campos.' : 'Revisei as informações e confirmo esta resposta para o atendimento.'} />
        {!['documento', 'mensagem'].includes(question?.tipo || '') && <Typography variant="caption">Sem confirmação, a resposta é salva como informada e continua pendente.</Typography>}
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button onClick={() => setQuestion(null)} disabled={busy}>Manter pendente</Button>
        <Button variant="contained" onClick={send} disabled={busy || !reason.trim() || (['documento', 'mensagem'].includes(question?.tipo || '') ? !confirm : !value.trim())}>{busy ? 'Salvando…' : 'Registrar resposta'}</Button></DialogActions>
    </Dialog>
  </>
}
