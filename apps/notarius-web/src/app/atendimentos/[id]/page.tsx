'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Tab, Tabs, TextField, ThemeProvider, Typography, createTheme, useTheme } from '@mui/material'
import { MainLayout } from '@/components/layout/main-layout'
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

export default function AtendimentoPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuthStore()
  const { selectedTenant } = useTenantStore()
  return <ConteudoAtendimento key={[id, user?.id, selectedTenant?.id].join(':')} id={id} />
}

function ConteudoAtendimento({ id }: { id: string }) {
  const { user } = useAuthStore()
  const { selectedTenant } = useTenantStore()
  const cache = useQueryClient()
  const [section, setSection] = useState(0)
  const outerTheme = useTheme()
  const pageTheme = useMemo(() => createTheme(outerTheme, {
    typography: { body1: { fontSize: '1.0625rem', lineHeight: 1.65 }, body2: { fontSize: '1rem', lineHeight: 1.6 }, caption: { fontSize: '.875rem', lineHeight: 1.5 }, button: { fontSize: '1rem', textTransform: 'none', fontWeight: 600 } },
    components: {
      MuiButton: { styleOverrides: { root: { minHeight: 46, borderRadius: 10, paddingInline: 18 }, sizeSmall: { minHeight: 44, fontSize: '.9375rem' } } },
      MuiInputBase: { styleOverrides: { input: { fontSize: '1.0625rem' } } },
      MuiDialog: { styleOverrides: { paper: { borderRadius: 16 } } },
      MuiDialogTitle: { styleOverrides: { root: { fontSize: '1.5rem', fontWeight: 650 } } },
      MuiDialogActions: { styleOverrides: { root: { padding: 20, gap: 8, flexWrap: 'wrap' } } },
    },
  }), [outerTheme])
  const scope = [id, user?.id, selectedTenant?.id]
  const compose = useRascunhoSessao(scope, 'mensagem', { texto: '', client_id: '', texto_tentado: '' }, mensagemValida)
  const texto = compose.value.texto
  const [pedidoFicha, setPedidoFicha] = useState<PedidoFicha | null>(null)
  const [pedidoDocumento, setPedidoDocumento] = useState<PedidoDocumento | null>(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<FonteDocumento | null>(null)
  const retry = useRef<{ texto: string; id: string } | null>(null)
  const messageScroll = useRef<HTMLDivElement | null>(null)
  useEffect(() => { setSelectedDocument(null); setSelectedMessageId(null); setSection(0) }, [id, user?.id, selectedTenant?.id])
  const enabled = !!user && !!selectedTenant
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
  const panel = { border: '1px solid', borderColor: '#dce4ee', borderRadius: 3, boxShadow: '0 2px 8px #18365b05', bgcolor: 'background.paper' }
  return <MainLayout><ThemeProvider theme={pageTheme}><Stack spacing={2} sx={{ maxWidth: 1180, mx: 'auto', minWidth: 0 }}>
    <Button component={Link} href="/atendimentos" sx={{ alignSelf: 'flex-start', color: 'text.secondary', px: 0, minHeight: 32 }}>← Todos os atendimentos</Button>
    {item.isLoading && <CircularProgress aria-label="Carregando atendimento" />}
    {item.isError && <Alert severity="error" action={<Button onClick={() => item.refetch()}>Tentar novamente</Button>}>Atendimento indisponível ou sem acesso neste cartório.</Alert>}
    {!selectedTenant && <Alert severity="warning">Selecione um cartório para continuar.</Alert>}
    {item.data && <>
      <Box component="header" sx={{ pb: 1 }}>
        <Stack direction="row" gap={2} justifyContent="space-between" alignItems="flex-start" flexWrap="wrap">
          <Box sx={{ minWidth: 0 }}><Typography sx={{ color: 'text.secondary', mb: .5, fontSize: 15 }}>Compra e venda</Typography>
            <Typography component="h1" sx={{ fontSize: { xs: 28, sm: 32 }, fontWeight: 700, lineHeight: 1.25, overflowWrap: 'anywhere' }}>{item.data.titulo}</Typography></Box>
          <Chip label={situacoesAtendimento[item.data.situacao]} sx={{ bgcolor: '#eaf0f6', color: '#334155', fontSize: 14, fontWeight: 600, height: 34 }} />
        </Stack>
      </Box>
      <Paper elevation={0} sx={{ ...panel, overflow: 'hidden' }}>
        <Tabs value={section} onChange={(_, value) => setSection(value)} variant="fullWidth" aria-label="Áreas do atendimento"
          sx={{ minHeight: 68, '& .MuiTabs-indicator': { height: 3 }, '& .MuiTab-root': { minHeight: 68, minWidth: 0, fontSize: { xs: 16, sm: 18 }, fontWeight: 650, textTransform: 'none', px: 1 }, '& .Mui-selected': { bgcolor: '#edf5ff' } }}>
          <Tab id="tab-conversa" aria-controls="painel-conversa" label="Conversa" />
          <Tab id="tab-documentos" aria-controls="painel-documentos" label="Documentos" />
          <Tab id="tab-minuta" aria-controls="painel-minuta" label="Minuta" />
        </Tabs>
      </Paper>
      <Box role="tabpanel" id="painel-conversa" aria-labelledby="tab-conversa" hidden={section !== 0}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 1fr) 320px' }, gap: 2.5, alignItems: 'start' }}>
          <Paper elevation={0} sx={{ ...panel, overflow: 'hidden' }}>
            <Box sx={{ px: { xs: 2, sm: 3 }, pt: 3, pb: 2, borderBottom: '1px solid #e7edf4' }}>
              <Typography component="h2" sx={{ fontSize: 22, fontWeight: 650 }}>Conversa do atendimento</Typography>
              <Typography color="text.secondary" sx={{ mt: .5 }}>Conte sobre o atendimento ou complemente as informações.</Typography>
            </Box>
            <Stack ref={messageScroll} spacing={2} sx={{ display: messages.data?.length === 0 && !messages.isError ? 'none' : 'flex', p: { xs: 2, sm: 3 }, maxHeight: { xs: 260, md: 320 }, overflowY: 'auto' }} role="log" aria-live="polite" aria-relevant="additions" aria-label="Mensagens salvas">
              {messages.isLoading && <CircularProgress aria-label="Carregando mensagens" />}
              {messages.isError && <Alert severity="error" action={<Button onClick={() => messages.refetch()}>Tentar novamente</Button>}>Não foi possível carregar a conversa.</Alert>}
              {messages.data?.map(m => <Box key={m.id} sx={{ bgcolor: '#f6f9fd', p: 2, border: '1px solid #e2eaf3', borderRadius: 2 }}>
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
                <TextField label="Escreva sua mensagem" placeholder="Conte aqui o que você já sabe sobre este atendimento…" multiline minRows={3} value={texto} disabled={sending}
                  onChange={e => compose.save(old => ({ ...old, texto: e.target.value }))} slotProps={{ htmlInput: { maxLength: 10000 } }} helperText="Rascunho guardado somente nesta aba do navegador. A mensagem só entra no atendimento ao clicar em Enviar." fullWidth />
                {compose.aviso && <Alert severity="warning">{compose.aviso}</Alert>}
                {error && <Alert severity="error" role="alert">{error}</Alert>}
                <Stack direction="row" justifyContent="space-between" alignItems="center" gap={1}><Typography variant="caption" color="text.secondary">{texto.length}/10000</Typography>
                  <Button type="submit" variant="contained" disableElevation disabled={sending || !compose.ready || !texto.trim() || !messages.isSuccess}>{sending ? 'Salvando…' : 'Enviar mensagem'}</Button>
                </Stack>
              </Stack>
            </Box>
          </Paper>
          <Stack spacing={2} component="aside" aria-label="Orientação e dados do atendimento">
            <PerguntasConferencia key={`conferencia-${scope.join(':')}`} id={id} scope={scope} onAttach={showDocuments} onDraft={showDraft}
              onStructured={request => { setSelectedMessageId(null); setSelectedDocument(null); setSection(0); setPedidoFicha({ ...request, token: crypto.randomUUID() }) }}
              onReviewMessage={messageId => { setSelectedDocument(null); setSelectedMessageId(messageId) }} />
            <Paper elevation={0} sx={{ ...panel, p: 2.5 }}><Stack spacing={1}>
              <Typography component="h2" sx={{ fontSize: 19, fontWeight: 650 }}>Dados do atendimento</Typography>
              <Typography variant="body2" color="text.secondary">Confira o que foi registrado e de onde veio cada informação.</Typography>
              <FichaAtendimento key={scope.join(':')} id={id} scope={scope} messages={messages.data || []}
                pedido={pedidoFicha} onPedidoConsumido={() => setPedidoFicha(null)}
                selectedMessage={messages.data?.find(m => m.id === selectedMessageId) || null} selectedDocument={selectedDocument}
                onUsed={() => { setSelectedMessageId(null); setSelectedDocument(null) }} />
              <RevisaoGeral key={`resumo-${scope.join(':')}`} id={id} scope={scope} />
            </Stack></Paper>
          </Stack>
        </Box>
      </Box>
      <Box role="tabpanel" id="painel-documentos" aria-labelledby="tab-documentos" hidden={section !== 1}>
        <Paper elevation={0} sx={{ ...panel, p: { xs: 2, sm: 3 } }}><Stack spacing={3}>
          <Box><Typography component="h2" sx={{ fontSize: 24, fontWeight: 650 }}>Documentos do atendimento</Typography>
            <Typography color="text.secondary" sx={{ mt: .5 }}>Envie os arquivos e confira a leitura de cada documento.</Typography></Box>
          <AnexosConversa key={`anexos-${scope.join(':')}`} id={id} scope={scope} pedido={pedidoDocumento} onPedidoConsumido={() => setPedidoDocumento(null)} onSource={source => { setSection(0); setSelectedMessageId(null); setSelectedDocument(source) }} />
        </Stack></Paper>
      </Box>
      <Box role="tabpanel" id="painel-minuta" aria-labelledby="tab-minuta" hidden={section !== 2}>
        <Paper elevation={0} sx={{ ...panel, p: { xs: 2, sm: 3 } }}><Stack spacing={3}>
          <Box><Typography component="h2" sx={{ fontSize: 24, fontWeight: 650 }}>Minuta de compra e venda</Typography>
            <Typography color="text.secondary" sx={{ mt: .5 }}>Revise o modelo, prepare o texto e faça a conferência final antes de baixar.</Typography></Box>
          <PreparacaoMinuta key={`redacao-${scope.join(':')}`} id={id} scope={scope} />
          <Alert severity="info">A preparação depende dos dados conferidos e do modelo aprovado. Se houver algo pendente, volte à aba Conversa.</Alert>
        </Stack></Paper>
      </Box>
      <Accordion disableGutters elevation={0} sx={{ ...panel, '&:before': { display: 'none' }, overflow: 'hidden' }}>
        <AccordionSummary expandIcon={<span aria-hidden="true">⌄</span>} sx={{ px: 3, minHeight: 58 }}><Typography fontWeight={600}>Mais opções</Typography></AccordionSummary>
        <AccordionDetails sx={{ px: 3, pb: 3 }}><Stack spacing={2}>
          <OrganizacaoAtendimento key={`organizacao-${scope.join(':')}`} item={item.data} scope={scope} />
          <Box><FeedbackDoTeste key={`feedback-${scope.join(':')}`} id={id} scope={scope} /></Box>
        </Stack></AccordionDetails>
      </Accordion>
      <Typography variant="body2" color="text.secondary" sx={{ px: .5 }}>Você decide o que confirmar. Informações duvidosas devem permanecer pendentes.</Typography>
    </>}
  </Stack></ThemeProvider></MainLayout>
}
