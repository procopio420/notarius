'use client'

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type CampoFicha, type Mensagem, type SituacaoDado, type FonteDocumento, type PedidoFicha } from '@/lib/atendimentos'
import { FichaDetalhada } from './FichaDetalhada'

const labels: Record<SituacaoDado, string> = {
  ausente: 'Ausente', informado: 'Informado pela escrevente', confirmado: 'Confirmado pela escrevente',
  divergente: 'Divergente', ilegivel: 'Leitura incerta',
}

export function FichaAtendimento({ id, scope, messages, selectedMessage, selectedDocument, onUsed, pedido, onPedidoConsumido }: {
  pedido?: PedidoFicha | null; onPedidoConsumido?: () => void
  id: string; scope: (string | undefined)[]; messages: Mensagem[]
  selectedMessage: Mensagem | null; selectedDocument: FonteDocumento | null; onUsed: () => void
}) {
  const cache = useQueryClient()
  const query = useQuery({ queryKey: ['ficha-atendimento', ...scope], queryFn: () => atendimentosApi.ficha(id) })
  const [editing, setEditing] = useState<CampoFicha | null>(null)
  const [valor, setValor] = useState('')
  const [situacao, setSituacao] = useState<SituacaoDado>('informado')
  const [source, setSource] = useState('')
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<CampoFicha | null>(null)
  const [showFicha, setShowFicha] = useState(false)
  const [documentSource, setDocumentSource] = useState<FonteDocumento | null>(null)
  const [excerpt, setExcerpt] = useState('')
  const fields = query.data?.campos || []
  const pending = fields.filter(f => ['informado', 'divergente', 'ilegivel'].includes(f.atual?.situacao || '') || (f.obrigatorio && f.atual?.situacao !== 'confirmado'))

  function open(field: CampoFicha) {
    setEditing(field)
    const previous = field.atual?.origem
    const doc = selectedDocument || (!selectedMessage && previous?.tipo === 'documento' ? { organizacao_versao: previous.organizacao_versao, pagina_id: previous.pagina_id!, arquivo: previous.arquivo!, pagina: previous.pagina!, trecho: previous.trecho || '', canal: previous.canal || 'texto' } : null)
    setDocumentSource(doc)
    setExcerpt(doc?.trecho || '')
    setValor(selectedDocument?.trecho || selectedMessage?.texto || field.atual?.valor || '')
    setSource(doc ? 'documento' : selectedMessage?.id || previous?.mensagem_id || '')
    setSituacao(selectedMessage || selectedDocument ? 'informado' : field.atual?.situacao || 'informado')
    setReason('')
    setError('')
  }

  async function save() {
    if (!editing || saving) return
    setSaving(true)
    setError('')
    try {
      await atendimentosApi.updateField(id, { chave: editing.chave, valor: situacao === 'ausente' ? '' : valor.trim(),
        situacao, mensagem_id: source && source !== 'documento' ? source : null,
        organizacao_versao: source === 'documento' ? documentSource?.organizacao_versao : undefined,
        pagina_id: source === 'documento' ? documentSource?.pagina_id : null,
        trecho_origem: source === 'documento' ? excerpt.trim() : '',
        canal_origem: source === 'documento' ? documentSource?.canal || 'texto' : 'texto',
        justificativa: reason.trim(), versao_esperada: editing.atual?.versao || 0 })
      await cache.invalidateQueries({ queryKey: ['ficha-atendimento', ...scope] })
      await cache.invalidateQueries({ queryKey: ['atendimentos'] })
      await cache.invalidateQueries({ queryKey: ['conferencia-atendimento'] })
      await cache.invalidateQueries({ queryKey: ['minuta-atendimento'] })
      setEditing(null)
      setShowFicha(false)
      onUsed()
    } catch (err) {
      const status = (err as { response?: { status: number } }).response?.status
      setError(status === 409 ? 'O campo já foi atualizado. Feche esta janela, atualize a ficha e confira o histórico antes de tentar novamente.' : 'Não foi possível confirmar o salvamento. Seu texto foi mantido; consulte a ficha antes de repetir.')
    } finally { setSaving(false) }
  }

  return <Stack spacing={2}>
    <FichaDetalhada id={id} scope={scope} messages={messages} selectedMessage={selectedMessage} selectedDocument={selectedDocument} onUsed={onUsed} onLegacy={() => setShowFicha(true)} pedido={pedido} onPedidoConsumido={onPedidoConsumido} />
    <Button variant="outlined" onClick={() => setShowFicha(true)} sx={{ alignSelf: 'stretch' }}>Conteúdo antigo e blocos de redação</Button>
    <Dialog open={showFicha} onClose={() => { setShowFicha(false); onUsed() }} fullWidth maxWidth="md">
    <DialogTitle>Dados do atendimento</DialogTitle><DialogContent><Stack spacing={2}>
    {(selectedMessage || selectedDocument) ? <Stack spacing={2}>
      <Typography>Em qual informação você quer usar esse trecho?</Typography>
      <TextField select label="Informação do atendimento" value="" onChange={e => { const field = fields.find(f => f.chave === e.target.value); if (field) open(field) }}>
        {fields.map(f => <MenuItem key={f.chave} value={f.chave}>{f.rotulo}</MenuItem>)}
      </TextField>
      <Typography variant="body2" color="text.secondary">Você poderá conferir o valor e a origem antes de salvar.</Typography>
    </Stack> : <>
    {query.isLoading && <Typography>Carregando dados…</Typography>}
    {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não foi possível carregar os dados.</Alert>}
    {query.isSuccess && <Typography color="text.secondary">{pending.length ? `${pending.length} campo(s) precisam da sua conferência.` : 'Os campos iniciais foram confirmados.'} Abra um campo para conferir o valor e sua origem.</Typography>}
    <Paper elevation={0} sx={{ p: 0 }}><Stack spacing={2}>

      {(selectedMessage || selectedDocument) && <Alert severity="info" action={<Button onClick={onUsed}>Cancelar</Button>}>Origem selecionada. Escolha o campo em que deseja registrar a informação.</Alert>}
      {fields.map(field => <Box key={field.chave} sx={{ border: '1px solid #dce4ee', borderRadius: 2, p: 2 }}>
        <Typography fontWeight={600}>{field.rotulo}{field.obrigatorio ? ' · campo inicial' : ' · opcional'}</Typography>
        <Chip size="small" sx={{ my: 1 }} label={labels[field.atual?.situacao || 'ausente']} color={field.atual?.situacao === 'confirmado' ? 'success' : 'default'} />
        <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{field.atual?.valor || 'Sem informação registrada.'}</Typography>
        {field.atual && <Typography variant="caption" color="text.secondary">Origem: {field.atual.origem.tipo === 'documento' ? `${field.atual.origem.arquivo}, página ${field.atual.origem.pagina}` : field.atual.origem.tipo === 'mensagem' ? 'mensagem da conversa' : 'registro manual'} · versão {field.atual.versao}</Typography>}
        <Stack direction="row" spacing={1} sx={{ mt: 1 }}><Button size="small" variant="outlined" onClick={() => open(field)}>{selectedMessage || selectedDocument ? 'Usar neste campo' : 'Conferir campo'}</Button>
          <Button size="small" disabled={!field.historico.length} onClick={() => setHistory(field)}>Ver origem e histórico</Button></Stack>
      </Box>)}
      <Button onClick={() => query.refetch()}>Atualizar ficha</Button>
    </Stack></Paper>
    </>}
    </Stack></DialogContent><DialogActions><Button onClick={() => { setShowFicha(false); onUsed() }}>Voltar à conversa</Button></DialogActions></Dialog>
    <Dialog open={!!editing} onClose={() => !saving && setEditing(null)} fullWidth maxWidth="sm">
      <DialogTitle>{editing?.rotulo}</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <TextField select label="Origem" value={source || 'manual'} onChange={e => setSource(e.target.value === 'manual' ? '' : e.target.value)} disabled={saving}>
          <MenuItem value="manual">Informação registrada manualmente pela escrevente</MenuItem>
          {documentSource && <MenuItem value="documento">{documentSource.arquivo} · página {documentSource.pagina}</MenuItem>}
          {messages.map(m => <MenuItem value={m.id} key={m.id}>Mensagem: {m.texto.slice(0, 65)}</MenuItem>)}
        </TextField>
        {source && source !== 'documento' && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>Texto de origem: {messages.find(m => m.id === source)?.texto}</Typography>}
        {source === 'documento' && <TextField label="Trecho literal do documento" multiline minRows={3} value={excerpt} onChange={e => setExcerpt(e.target.value)} helperText="Mantenha somente um trecho que exista exatamente no texto extraído. Não o reescreva." disabled={saving} slotProps={{ htmlInput: { maxLength: 10000 } }} />}
        <TextField select label="Situação" value={situacao} onChange={e => setSituacao(e.target.value as SituacaoDado)} disabled={saving}>
          {Object.entries(labels).map(([key, label]) => <MenuItem value={key} key={key}>{label}</MenuItem>)}
        </TextField>
        <TextField label="Valor ou descrição da divergência" multiline minRows={3} value={valor} onChange={e => setValor(e.target.value)} disabled={saving || situacao === 'ausente'} slotProps={{ htmlInput: { maxLength: 10000 } }} />
        <TextField label="Motivo do registro ou da alteração" multiline minRows={2} value={reason} onChange={e => setReason(e.target.value)} disabled={saving} required slotProps={{ htmlInput: { maxLength: 2000 } }} />
        {situacao === 'confirmado' && <Alert severity="info">Esta confirmação é sua. O sistema não verificou a informação em documentos.</Alert>}
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent>
      <DialogActions><Button onClick={() => setEditing(null)} disabled={saving}>Cancelar</Button><Button variant="contained" onClick={save} disabled={saving || !reason.trim() || (['informado', 'confirmado', 'divergente'].includes(situacao) && !valor.trim())}>{saving ? 'Salvando…' : 'Salvar revisão'}</Button></DialogActions>
    </Dialog>
    <Dialog open={!!history} onClose={() => setHistory(null)} fullWidth maxWidth="sm"><DialogTitle>Origem e histórico · {history?.rotulo}</DialogTitle>
      <DialogContent><Stack spacing={3}>{history?.historico.map(r => <Box key={r.id}>
        <Typography fontWeight={600}>Versão {r.versao} · {labels[r.situacao]}</Typography>
        <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{r.valor || 'Sem valor'}</Typography>
        <Typography variant="body2">Motivo: {r.justificativa}</Typography>
        <Typography variant="body2">Origem: {r.origem.tipo === 'documento' ? `${r.origem.arquivo}, página ${r.origem.pagina}${r.origem.canal === 'ocr' ? ' · OCR' : ''}` : r.origem.tipo === 'mensagem' ? 'mensagem da conversa' : 'registro manual'}</Typography>
        {r.origem.trecho && <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>Trecho: {r.origem.trecho}</Typography>}
        <Typography variant="caption">{r.autor_nome || 'Escrevente'} · {new Date(r.created_at).toLocaleString('pt-BR')}</Typography>
      </Box>)}</Stack></DialogContent><DialogActions><Button onClick={() => setHistory(null)}>Fechar</Button></DialogActions>
    </Dialog>
  </Stack>
}
