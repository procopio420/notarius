'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Tab, Tabs, TextField, Typography } from '@mui/material'
import { ArrowLeft, ArrowRight, ChevronDown, ClipboardList, Files, FileText, MessageSquareText, SlidersHorizontal } from 'lucide-react'
import { FichaAtendimento } from '@/components/atendimentos/FichaAtendimento'
import { AnexosConversa } from '@/components/atendimentos/AnexosConversa'
import { PerguntasConferencia } from '@/components/atendimentos/PerguntasConferencia'
import { PreparacaoMinuta } from '@/components/atendimentos/MinutaPreparada'
import { InterpretacaoMensagem } from '@/components/atendimentos/InterpretacaoMensagem'
import { OrganizacaoAtendimento, situacoesAtendimento } from '@/components/atendimentos/OrganizacaoAtendimento'
import { RevisaoGeral } from '@/components/atendimentos/RevisaoGeral'
import { FeedbackDoTeste } from '@/components/atendimentos/FeedbackDoTeste'
import { atendimentosApi, type Mensagem, type FonteDocumento, type PedidoFicha, type PedidoDocumento } from '@/lib/atendimentos'
import { useRascunhoSessao, mensagemValida } from '@/lib/rascunhoSessao'
import { CorrecaoMensagem } from '@/components/atendimentos/CorrecaoMensagem'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'

export function FerramentasDoAtendimento({ id, documentoInicial = null }: { id: string; documentoInicial?: PedidoDocumento | null }) {
  const { user } = useAuthStore()
  const { selectedTenant } = useTenantStore()
  const cache = useQueryClient()
  const [section, setSection] = useState(documentoInicial ? 1 : 0)
  const workspace = process.env.NEXT_PUBLIC_PILOTO_LOCAL === '1' ? 'piloto-local' : selectedTenant?.id
  const scope = [id, user?.id, workspace]
  const compose = useRascunhoSessao(scope, 'mensagem-ferramentas', { texto: '', client_id: '', texto_tentado: '' }, mensagemValida)
  const texto = compose.value.texto
  const [pedidoFicha, setPedidoFicha] = useState<PedidoFicha | null>(null)
  const [pedidoDocumento, setPedidoDocumento] = useState<PedidoDocumento | null>(documentoInicial)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<FonteDocumento | null>(null)
  const retry = useRef<{ texto: string; id: string } | null>(null)
  const messageScroll = useRef<HTMLDivElement | null>(null)
  const enabled = !!user && !!workspace
  const item = useQuery({ queryKey: ['atendimento', ...scope], queryFn: () => atendimentosApi.get(id), enabled })
  const messageKey = ['mensagens-atendimento', ...scope]
  const messages = useQuery({ queryKey: messageKey, queryFn: () => atendimentosApi.messages(id), enabled: enabled && item.isSuccess, refetchOnWindowFocus: true })
  useEffect(() => {
    const list = messageScroll.current
    if (list && messages.data?.length) list.scrollTop = list.scrollHeight
  }, [id, messages.data?.length])

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const content = texto
    if (!content.trim() || sending || !compose.ready) return
    const clientId = compose.value.texto_tentado === content && compose.value.client_id ? compose.value.client_id : retry.current?.texto === content ? retry.current.id : crypto.randomUUID()
    compose.save({ texto: content, texto_tentado: content, client_id: clientId })
    retry.current = { texto: content, id: clientId }
    setSending(true)
    setError('')
    try {
      const saved = await atendimentosApi.send(id, content, clientId)
      cache.setQueryData<Mensagem[]>(messageKey, old => [...(old || []).filter(m => m.id !== saved.id), saved])
      compose.clear()
      retry.current = null
      await cache.invalidateQueries({ queryKey: ['atendimentos'] })
      await cache.invalidateQueries({ queryKey: ['conferencia-atendimento'] })
      await cache.invalidateQueries({ queryKey: ['minuta-atendimento'] })
      await cache.invalidateQueries({ queryKey: ['roteiro-conversa'] })
    } catch {
      setError('Não foi possível confirmar o envio. O texto foi mantido; tente novamente. Reenviar o mesmo texto não duplica a mensagem.')
    } finally { setSending(false) }
  }

  function showDocuments(request?: Omit<PedidoDocumento, 'token'>) {
    setPedidoDocumento(request ? { ...request, token: crypto.randomUUID() } : null)
    setSection(1)
    requestAnimationFrame(() => {
      document.getElementById('tab-documentos')?.focus()
      document.getElementById('anexar-arquivo')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
  function showDraft() {
    setSection(2)
    requestAnimationFrame(() => document.getElementById('tab-minuta')?.focus())
  }
  const panel = { border: '1px solid #e3e8df', borderRadius: '18px', bgcolor: 'background.paper' }
  return <Stack spacing={3} sx={{ minWidth: 0 }}>
    <Button component={Link} href="/atendimentos" startIcon={<ArrowLeft size={15} />} sx={{ alignSelf: 'flex-start', color: 'text.secondary', px: 0, minHeight: 28, fontSize: 12 }}>Atendimentos</Button>
    {item.isLoading && <CircularProgress size={24} aria-label="Carregando atendimento" />}
    {item.isError && <Alert severity="error" action={<Button onClick={() => item.refetch()}>Tentar novamente</Button>}>Atendimento indisponível ou sem acesso nesta conta.</Alert>}
    {!enabled && <Alert severity="info">Preparando seu espaço de trabalho…</Alert>}
    {item.data && <>
      <Stack component="header" direction="row" gap={2} justifyContent="space-between" alignItems="flex-start">
        <Box sx={{ minWidth: 0 }}><Typography sx={{ fontSize: 10, fontWeight: 700, letterSpacing: '1.6px', color: '#7c896f', mb: 1 }}>COMPRA E VENDA</Typography>
          <Typography component="h1" sx={{ fontFamily: 'Georgia, serif', fontSize: { xs: 30, sm: 38 }, lineHeight: 1.2, letterSpacing: '-.8px', overflowWrap: 'anywhere' }}>{item.data.titulo}</Typography>
          <Typography sx={{ fontSize: 12, color: 'text.secondary', mt: 1 }}>Um caso, todos os documentos e cada informação no lugar.</Typography>
        </Box>
        <Chip label={situacoesAtendimento[item.data.situacao]} sx={{ flexShrink: 0, mt: .5, bgcolor: '#eaf1e4', color: '#41623d', fontSize: 10, maxWidth: { xs: 105, sm: 'none' }, '& .MuiChip-label': { whiteSpace: 'normal', lineHeight: 1.2 } }} />
      </Stack>
      <Tabs value={section} onChange={(_, value) => setSection(value)} variant="fullWidth" aria-label="Etapas do atendimento" sx={{ borderBottom: '1px solid #dce3d7', '& .MuiTab-root': { minHeight: 64, px: 1, fontSize: { xs: 12, sm: 14 }, gap: 1, flexDirection: 'row', '&.Mui-selected': { color: '#254c40' } } }}>
        <Tab id="tab-conversa" aria-controls="painel-conversa" icon={<ClipboardList size={18} />} label="Dados do caso" />
        <Tab id="tab-documentos" aria-controls="painel-documentos" icon={<Files size={18} />} label="Documentos" />
        <Tab id="tab-minuta" aria-controls="painel-minuta" icon={<FileText size={18} />} label="Minuta" />
      </Tabs>
      <Box role="tabpanel" id="painel-conversa" aria-labelledby="tab-conversa" hidden={section !== 0}>
        <Stack spacing={2.5}>
          <PerguntasConferencia key={`conferencia-${scope.join(':')}`} id={id} scope={scope} onAttach={showDocuments} onDraft={showDraft}
            onStructured={request => { setSelectedMessageId(null); setSelectedDocument(null); setSection(0); setPedidoFicha({ ...request, token: crypto.randomUUID() }) }}
            onReviewMessage={messageId => { setSelectedDocument(null); setSelectedMessageId(messageId) }} />
          <Paper sx={{ ...panel, p: { xs: 2.5, sm: 3.5 } }}>
            <Stack direction="row" gap={2} alignItems="flex-start" sx={{ mb: 2.5 }}>
              <Box sx={{ p: 1.5, bgcolor: '#eef3e8', color: '#526b47', borderRadius: '12px', display: 'flex' }}><ClipboardList size={22} strokeWidth={1.5} /></Box>
              <Box><Typography component="h2" sx={{ fontSize: 19, fontWeight: 650 }}>Pessoas, imóvel e negócio</Typography><Typography sx={{ fontSize: 13, color: 'text.secondary', mt: .5 }}>Preencha a ficha e confira a fonte de cada informação.</Typography></Box>
            </Stack>
            <FichaAtendimento key={scope.join(':')} id={id} scope={scope} messages={messages.data || []}
              pedido={pedidoFicha} onPedidoConsumido={() => setPedidoFicha(null)}
              selectedMessage={messages.data?.find(m => m.id === selectedMessageId) || null} selectedDocument={selectedDocument}
              onUsed={() => { setSelectedMessageId(null); setSelectedDocument(null) }} />
          </Paper>
          <Accordion sx={{ ...panel }}>
            <AccordionSummary expandIcon={<ChevronDown size={17} />}><Stack direction="row" gap={1.5} alignItems="center"><MessageSquareText size={18} /><Box><Typography fontWeight={600} fontSize={14}>Anotações e conversa</Typography><Typography color="text.secondary" fontSize={12}>{messages.data?.length ? `${messages.data.length} registro(s) no histórico` : 'Informações recebidas e observações sobre o caso'}</Typography></Box></Stack></AccordionSummary>
            <AccordionDetails sx={{ p: 0 }}>            <Stack ref={messageScroll} spacing={2} sx={{ display: messages.data?.length === 0 && !messages.isError ? 'none' : 'flex', p: { xs: 2, sm: 3 }, maxHeight: { xs: 260, md: 320 }, overflowY: 'auto' }} role="log" aria-live="polite" aria-relevant="additions" aria-label="Mensagens salvas">
              {messages.isLoading && <CircularProgress aria-label="Carregando mensagens" />}
              {messages.isError && <Alert severity="error" action={<Button onClick={() => messages.refetch()}>Tentar novamente</Button>}>Não foi possível carregar a conversa.</Alert>}
              {messages.data?.map(m => <Box key={m.id} sx={{ bgcolor: '#f7f8f3', p: 2, border: '1px solid #e2eaf3', borderRadius: 2 }}>
                <Stack direction="row" justifyContent="space-between" gap={1} flexWrap="wrap"><Typography variant="caption" fontWeight={650}>{m.autor_nome || 'Escrevente'}</Typography><Typography variant="caption" color="text.secondary">{new Date(m.created_at).toLocaleString('pt-BR')}</Typography></Stack>
                {m.pergunta && <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Resposta a: {m.pergunta}</Typography>}
                {m.correcao_de && <Typography variant="body2">Correção da mensagem {m.correcao_de.slice(0, 8)} · {m.motivo_correcao}</Typography>}
                {messages.data?.some(n => n.correcao_de === m.id) && <Alert severity="warning">Mensagem corrigida posteriormente. Original preservado para histórico; use a última resposta para nova revisão.</Alert>}
                <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', my: 1 }}>{m.texto}</Typography>
                <Accordion disableGutters elevation={0} sx={{ bgcolor: 'transparent', '&:before': { display: 'none' } }}>
                  <AccordionSummary expandIcon={<span aria-hidden="true">⌄</span>} sx={{ px: 0, minHeight: 44 }}><Typography variant="body2" color="primary.main">Opções desta mensagem</Typography></AccordionSummary>
                  <AccordionDetails sx={{ p: 0 }}><Stack alignItems="flex-start">
                    <Button disabled={!!messages.data?.some(n => n.correcao_de === m.id)} onClick={() => { setSelectedDocument(null); setSelectedMessageId(m.id) }}>Usar nos dados do atendimento</Button>
                    {!messages.data?.some(n => n.correcao_de === m.id) && <InterpretacaoMensagem id={id} mensagem={m} onReview={() => { setSelectedDocument(null); setSelectedMessageId(m.id) }} />}
                    <CorrecaoMensagem id={id} scope={scope} mensagem={m} substituida={!!messages.data?.some(n => n.correcao_de === m.id)} />
                  </Stack></AccordionDetails>
                </Accordion>
              </Box>)}
            </Stack>
            <Box component="form" onSubmit={send} sx={{ p: { xs: 2, sm: 3 }, borderTop: '1px solid #e7edf4' }}>
              <Stack spacing={1.5}>
                <TextField label="Anotação do atendimento" placeholder="Registre uma informação recebida ou uma observação sobre o caso…" multiline minRows={2} value={texto} disabled={sending}
                  onChange={e => compose.save(old => ({ ...old, texto: e.target.value }))} slotProps={{ htmlInput: { maxLength: 10000 } }} helperText="Clique em Salvar anotação para registrar. O rascunho fica somente nesta aba." fullWidth />
                {compose.aviso && <Alert severity="warning">{compose.aviso}</Alert>}
                {error && <Alert severity="error" role="alert">{error}</Alert>}
                <Stack direction="row" justifyContent="space-between" alignItems="center" gap={1}><Typography variant="caption" color="text.secondary">{texto.length}/10000</Typography>
                  <Button type="submit" variant="contained" disableElevation disabled={sending || !compose.ready || !texto.trim() || !messages.isSuccess}>{sending ? 'Salvando…' : 'Salvar anotação'}</Button>
                </Stack>
              </Stack>
            </Box>

            </AccordionDetails>
          </Accordion>
          <Accordion sx={{ ...panel }}>
            <AccordionSummary expandIcon={<ChevronDown size={17} />}><Typography fontSize={14} fontWeight={600}>Resumo da conferência</Typography></AccordionSummary>
            <AccordionDetails><RevisaoGeral key={`resumo-${scope.join(':')}`} id={id} scope={scope} /></AccordionDetails>
          </Accordion>
          <Stack direction="row" justifyContent="flex-end"><Button endIcon={<ArrowRight size={16} />} onClick={() => showDocuments()}>Ir para documentos</Button></Stack>
        </Stack>
      </Box>
      <Box role="tabpanel" id="painel-documentos" aria-labelledby="tab-documentos" hidden={section !== 1}>
        <Paper sx={{ ...panel, p: { xs: 2.5, sm: 3.5 } }}><Stack spacing={3}>
          <Box><Typography component="h2" sx={{ fontSize: 22, fontWeight: 650 }}>Documentos do caso</Typography><Typography color="text.secondary" sx={{ mt: .5, fontSize: 13 }}>Anexe os arquivos e confira a leitura antes de usar os dados.</Typography></Box>
          <AnexosConversa key={`anexos-${scope.join(':')}`} id={id} scope={scope} pedido={pedidoDocumento} onPedidoConsumido={() => setPedidoDocumento(null)} onSource={source => { setSection(0); setSelectedMessageId(null); setSelectedDocument(source) }} />
          <Stack direction="row" justifyContent="space-between" gap={1}><Button startIcon={<ArrowLeft size={15} />} onClick={() => setSection(0)}>Dados do caso</Button><Button endIcon={<ArrowRight size={15} />} onClick={showDraft}>Ir para minuta</Button></Stack>
        </Stack></Paper>
      </Box>
      <Box role="tabpanel" id="painel-minuta" aria-labelledby="tab-minuta" hidden={section !== 2}>
        <Paper sx={{ ...panel, p: { xs: 2.5, sm: 3.5 } }}><Stack spacing={3}>
          <Box><Typography component="h2" sx={{ fontSize: 22, fontWeight: 650 }}>Sua minuta</Typography><Typography color="text.secondary" sx={{ mt: .5, fontSize: 13 }}>Prepare o texto, revise e exporte a versão conferida.</Typography></Box>
          <PreparacaoMinuta key={`redacao-${scope.join(':')}`} id={id} scope={scope} />
        </Stack></Paper>
      </Box>
      <Accordion sx={{ bgcolor: 'transparent', border: 'none !important', '& .MuiAccordionSummary-root': { px: 0 } }}>
        <AccordionSummary expandIcon={<ChevronDown size={16} />}><Stack direction="row" gap={1} alignItems="center" sx={{ color: 'text.secondary' }}><SlidersHorizontal size={15} /><Typography fontSize={12}>Organizar atendimento e registrar feedback</Typography></Stack></AccordionSummary>
        <AccordionDetails><Stack spacing={2}>
          <OrganizacaoAtendimento key={`organizacao-${scope.join(':')}`} item={item.data} scope={scope} />
          <Box><FeedbackDoTeste key={`feedback-${scope.join(':')}`} id={id} scope={scope} /></Box>
        </Stack></AccordionDetails>
      </Accordion>
    </>}
  </Stack>
}
