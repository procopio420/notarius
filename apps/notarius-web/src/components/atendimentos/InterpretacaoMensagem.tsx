'use client'
import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Typography } from '@mui/material'
import { type Mensagem } from '@/lib/atendimentos'
import { propostasDadosApi, situacoesProposta, type PropostaEvidencia, type ExtracaoPropostas } from '@/lib/propostasDados'

export function InterpretacaoMensagem({ id, mensagem, onReview }: { id: string; mensagem: Mensagem; onReview: () => void }) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<ExtracaoPropostas | null>(null)
  const [proposals, setProposals] = useState<PropostaEvidencia[]>([])
  const retry = useRef<string | null>(null)
  async function analyze() {
    if (busy) return
    retry.current ||= crypto.randomUUID()
    setBusy(true); setError('')
    try {
      const saved = await propostasDadosApi.extrair(id, { mensagem_id: mensagem.id }, retry.current)
      setResult(saved)
      const all = await propostasDadosApi.get(id)
      setProposals(all.propostas.filter(p => saved.propostas_ids.includes(p.id)))
      await Promise.all(['ficha-detalhada', 'propostas-dados', 'conferencia-atendimento', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
    } catch { setError('Não foi possível concluir o registro das propostas. Atualize antes de tentar novamente; nenhum dado foi confirmado.') }
    finally { setBusy(false) }
  }
  return <>
    <Button size="small" onClick={() => { setOpen(true); setError('') }}>Propostas locais da mensagem</Button>
    <Dialog open={open} onClose={() => !busy && setOpen(false)} fullWidth maxWidth="sm">
      <DialogTitle>Propostas locais com fonte</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Typography>Rótulos explícitos como “Nome:”, “CPF:” e “Preço:” geram propostas guardadas para revisão. Não é IA real; nenhum dado é enviado a provedores externos. Nenhuma pessoa é associada ou confirmada automaticamente.</Typography>
        <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: 180, overflow: 'auto', bgcolor: 'action.hover', p: 2 }}>{mensagem.texto}</Typography>
        {error && <Alert severity="warning">{error}</Alert>}
        {result && <>
          <Alert severity="warning">{result.aviso} Linhas não interpretadas: {result.linhas_nao_interpretadas}.</Alert>
          {proposals.map(p => <Box key={p.id} sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography fontWeight={600}>{p.rotulo} · {situacoesProposta[p.situacao] || p.situacao}</Typography>
            <Typography sx={{ whiteSpace: 'pre-wrap' }}>{p.valor_original}</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Trecho literal: {p.trecho}</Typography>
          </Box>)}
          {!proposals.length && <Typography>Nenhum rótulo utilizável foi localizado. Confira a mensagem manualmente.</Typography>}
          <Button onClick={() => { setOpen(false); onReview() }}>Conferir propostas na ficha detalhada</Button>
        </>}
      </Stack></DialogContent>
      <DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Voltar</Button><Button disabled={busy} onClick={analyze}>{busy ? 'Aguarde…' : 'Guardar propostas para revisão'}</Button></DialogActions>
    </Dialog>
  </>
}
