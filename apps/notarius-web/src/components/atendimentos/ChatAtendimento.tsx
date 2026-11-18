'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Avatar, Box, Button, CircularProgress, Dialog, DialogContent, DialogTitle, IconButton, Stack, TextField, Typography } from '@mui/material'
import { ArrowLeft, ArrowUp, Download, FileText, MessageCircle, Paperclip, SlidersHorizontal, X } from 'lucide-react'
import { AtendimentoLayout } from './AtendimentoLayout'
import { EditorMinuta } from './EditorMinuta'
import { FerramentasDoAtendimento } from './FerramentasDoAtendimento'
import { ConferenciaAnexosChat } from './ConferenciaAnexosChat'
import { FontesDaMinutaChat } from './FontesDaMinutaChat'
import { AjusteMinutaChat } from './AjusteMinutaChat'
import { atendimentosApi, type Mensagem, type MinutaPreparada, type PedidoDocumento } from '@/lib/atendimentos'
import { pendenciasLeitura, resumoLeituraLocal, textoDosDocumentos } from '@/lib/chatAtendimento'
import { interpretarPedidoDeAjuste } from '@/lib/ajusteMinuta'
import { mensagemValida, useRascunhoSessao } from '@/lib/rascunhoSessao'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'

function txt(name: string, content: string) {
  const url = URL.createObjectURL(new Blob(['\uFEFF', content], { type: 'text/plain;charset=utf-8' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function Assistente({ children }: { children: React.ReactNode }) {
  return <Stack direction="row" gap={1.5} alignItems="flex-start">
    <Avatar aria-hidden="true" sx={{ width: 30, height: 32, bgcolor: '#254c40', color: '#e3efce', borderRadius: '9px', fontFamily: 'Georgia, serif', fontSize: 21 }}>N</Avatar>
    <Box sx={{ minWidth: 0, flex: 1 }}><Typography sx={{ fontSize: 11, color: '#708167', fontWeight: 650, mb: 1 }}>Notarius</Typography>{children}</Box>
  </Stack>
}

export function ChatAtendimento({ id }: { id: string }) {
  const { user } = useAuthStore()
  const { selectedTenant } = useTenantStore()
  const workspace = process.env.NEXT_PUBLIC_PILOTO_LOCAL === '1' ? 'piloto-local' : selectedTenant?.id
  const scope = [id, user?.id, workspace]
  const enabled = !!user && !!workspace
  const cache = useQueryClient()
  const item = useQuery({ queryKey: ['atendimento', ...scope], queryFn: () => atendimentosApi.get(id), enabled })
  const messages = useQuery({ queryKey: ['mensagens-atendimento', ...scope], queryFn: () => atendimentosApi.messages(id), enabled: enabled && item.isSuccess })
  const files = useQuery({ queryKey: ['anexos-atendimento', ...scope], queryFn: () => atendimentosApi.anexos(id), enabled: enabled && item.isSuccess })
  const draft = useQuery({ queryKey: ['minuta-atendimento', ...scope], queryFn: () => atendimentosApi.redacao(id), enabled: enabled && item.isSuccess })
  const assistida = !!draft.data?.minuta_assistida
  const usaGpt = draft.data?.provedor_minuta_assistida === 'openai'
  const comparisonKey = ['comparacao-anexos', ...scope]
  const comparison = useQuery({
    queryKey: [...comparisonKey, files.data?.map(file => [file.id, file.leitura_versao, file.organizacao?.versao])],
    queryFn: () => atendimentosApi.compararAnexos(id),
    enabled: enabled && item.isSuccess && !!files.data?.length && draft.isSuccess && !assistida,
  })
  const ai = useQuery({ queryKey: ['chat-ia', ...scope], queryFn: () => atendimentosApi.chatIA(id), enabled: enabled && item.isSuccess, retry: false })
  const compose = useRascunhoSessao(scope, 'mensagem', { texto: '', client_id: '', texto_tentado: '' }, mensagemValida)
  const [sending, setSending] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState('')
  const [error, setError] = useState('')
  const [unconfirmedAnswer, setUnconfirmedAnswer] = useState<string | null>(null)
  const [tools, setTools] = useState<true | PedidoDocumento | null>(null)
  const [minutaAberta, setMinutaAberta] = useState<MinutaPreparada | null>(null)
  const [ajuste, setAjuste] = useState<(NonNullable<ReturnType<typeof interpretarPedidoDeAjuste>> & { texto: string; minuta: MinutaPreparada }) | null>(null)
  const input = useRef<HTMLInputElement>(null)
  const end = useRef<HTMLDivElement>(null)
  const attempted = useRef<{ texto: string; id: string } | null>(null)
  const report = resumoLeituraLocal(files.data || [])
  const readingQuestions = pendenciasLeitura(files.data || [])
  const current = draft.data?.versoes[0]
  const arquivosDoCaso = files.data?.filter(file => usaGpt
    ? file.organizacao?.finalidade === 'caso' && file.organizacao.leitura_atual
    : !['referencia_redacao', 'nao_utilizar'].includes(file.organizacao?.finalidade || '')) || []
  const conference = useQuery({ queryKey: ['conferencia-atendimento', ...scope], queryFn: () => atendimentosApi.roteiro(id), enabled: enabled && (!!ajuste || !!current?.desatualizada) })
  const affected = conference.data?.pendencias.filter(question => !!current?.dados[question.chave]
    && question.candidatos.some(candidate => candidate.origem === 'documento')) || []
  const busy = sending || uploading || preparing
  const hasText = files.data?.some(file => file.paginas.some(p => p.texto.trim() || p.texto_ocr?.trim()))
  const aiStatus = usaGpt ? 'Ao preparar a minuta, apenas o texto das páginas selecionadas como fontes do caso pode ser enviado à API da OpenAI para extrair dados.'
    : assistida ? 'Preparação da minuta com IA local'
    : ai.isError ? 'Não foi possível consultar a IA. As mensagens podem ser salvas sem análise.'
    : ai.isPending ? 'Consultando a disponibilidade da IA…'
      : ai.data.habilitado ? 'IA conectada · GPT-6 Luna. Cada mensagem enviada pode consumir créditos, dentro do teto acumulado de testes de US$ 0,50. Sugestões exigem sua conferência.'
        : 'Modo local. A IA não está disponível; arquivos e mensagens podem ser guardados sem análise por IA.'
  const answerUnconfirmed = unconfirmedAnswer && !ai.data?.respostas.some(answer => answer.mensagem_id === unconfirmedAnswer)

  function closeTools() {
    setTools(null)
    void cache.invalidateQueries({ queryKey: comparisonKey })
  }

  useEffect(() => {
    if (messages.data?.length || ajuste) end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.data?.length, ajuste])

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const content = compose.value.texto
    if (!content.trim() || busy || !compose.ready || !messages.isSuccess) return
    if (/^(?:prepare|preparar) a minuta[.!]?$/i.test(content.trim())) {
      if (await prepararMinuta()) compose.clear()
      return
    }
    const pedido = interpretarPedidoDeAjuste(content)
    if (pedido) {
      if (!current) { setError('Prepare a primeira minuta antes de pedir um ajuste pelo chat.'); return }
      setAjuste({ ...pedido, texto: content, minuta: current }); setError(''); compose.clear()
      return
    }
    const clientId = compose.value.texto_tentado === content && compose.value.client_id ? compose.value.client_id : attempted.current?.texto === content ? attempted.current.id : crypto.randomUUID()
    attempted.current = { texto: content, id: clientId }
    compose.save({ texto: content, client_id: clientId, texto_tentado: content })
    setSending(true); setError('')
    try {
      const saved = await atendimentosApi.send(id, content, clientId)
      cache.setQueryData<Mensagem[]>(['mensagens-atendimento', ...scope], old => [...(old || []).filter(m => m.id !== saved.id), saved])
      compose.clear(); attempted.current = null
      if (ai.isSuccess && ai.data.habilitado) {
        setProgress('Conferindo os documentos e preparando a resposta…')
        try {
          const result = await atendimentosApi.responderIA(id, saved.id)
          cache.setQueryData(['chat-ia', ...scope], result)
        } catch {
          setUnconfirmedAnswer(saved.id)
          void ai.refetch()
        } finally { setProgress('') }
      }
      await Promise.all(['atendimentos', 'conferencia-atendimento', 'minuta-atendimento', 'roteiro-conversa'].map(key => cache.invalidateQueries({ queryKey: [key] })))
    } catch { setError('Não foi possível confirmar o envio. Seu texto foi mantido. Tentar novamente com o mesmo texto não duplica a mensagem.') }
    finally { setSending(false) }
  }
  async function prepararMinuta() {
    if (busy) return false
    if (current && !current.desatualizada && !draft.isError) {
      setError('')
      setMinutaAberta(current)
      return true
    }
    const state = draft.data
    if (!state || draft.isError || (assistida ? !arquivosDoCaso.length : !state.pronto || !state.modelo_aprovado)) {
      if (assistida) {
        setError(usaGpt ? 'Classifique os documentos legíveis como fontes do caso em “Revisão e ajustes”.' : 'Anexe os documentos deste atendimento para preparar a minuta.')
        return false
      }
      setError('Para preparar a minuta, confira o modelo e resolva as pendências do atendimento.')
      return false
    }
    setPreparing(true); setError('')
    try {
      const result = assistida
        ? await atendimentosApi.prepararMinutaAssistida(id, state.assinatura, current?.id ?? null)
        : await atendimentosApi.prepararMinuta(id, state.assinatura)
      cache.setQueryData(['minuta-atendimento', ...scope], result)
      const saved = result.versoes[0]
      if (!saved || saved.desatualizada) throw new Error('Minuta indisponível')
      setMinutaAberta(saved)
      return true
    } catch (err) {
      const data = (err as { response?: { data?: unknown } }).response?.data
      setError(Array.isArray(data) ? data.join(' ') : typeof data === 'object' && data && 'detail' in data
        ? String(data.detail) : 'Não foi possível confirmar a preparação. Confira as versões salvas antes de tentar novamente.')
      void draft.refetch()
      return false
    } finally { setPreparing(false) }
  }
  async function upload(incoming: FileList | null) {
    if (!incoming?.length || busy || !item.isSuccess) return
    const list = Array.from(incoming)
    if (list.length > 20 || list.some(file => !/\.(pdf|txt|png|jpe?g)$/i.test(file.name) || file.size > 10 * 1024 * 1024 || !file.size)) {
      setError('Selecione até 20 arquivos PDF, TXT, PNG ou JPG, com até 10 MB por arquivo.'); return
    }
    setUploading(true); setError('')
    let received = 0
    try {
      for (const file of list) {
        setProgress(`Recebendo ${received + 1} de ${list.length}: ${file.name}`)
        await atendimentosApi.upload(id, file); received++
      }
    } catch { setError(`${received} arquivo(s) enviado(s) nesta tentativa. O restante não foi confirmado. Confira os anexos e selecione novamente os arquivos pendentes; documentos idênticos não são duplicados.`) }
    finally {
      await Promise.all(['anexos-atendimento', 'conferencia-atendimento', 'minuta-atendimento', 'atendimentos'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      setUploading(false); setProgress('')
    }
  }
  return <AtendimentoLayout>
    <Stack sx={{ maxWidth: 820, mx: 'auto', minHeight: '70vh' }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" gap={1} sx={{ mb: 3 }}>
        <Button component={Link} href="/atendimentos" startIcon={<ArrowLeft size={15} />} sx={{ px: 0, color: 'text.secondary', fontSize: 12 }}>Atendimentos</Button>
        <Button startIcon={<SlidersHorizontal size={15} />} onClick={() => setTools(true)} disabled={!item.isSuccess} sx={{ fontSize: 12 }}>Revisão e ajustes</Button>
      </Stack>
      {item.isLoading && <CircularProgress aria-label="Abrindo conversa" size={24} />}
      {item.isError && <Alert severity="error" action={<Button onClick={() => item.refetch()}>Tentar novamente</Button>}>Não foi possível abrir este atendimento.</Alert>}
      {item.data && <>
        <Box sx={{ mb: 3.5 }}><Typography sx={{ color: '#7c896f', fontSize: 10, letterSpacing: '1.5px', fontWeight: 700, mb: 1 }}>COMPRA E VENDA</Typography><Typography component="h1" sx={{ fontFamily: 'Georgia, serif', fontSize: { xs: 30, sm: 38 }, lineHeight: 1.2, overflowWrap: 'anywhere' }}>{item.data.titulo}</Typography></Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1.25, px: 1.5, mb: 3, bgcolor: '#edf2e6', borderRadius: '10px' }}><MessageCircle size={15} style={{ flexShrink: 0 }} /><Typography fontSize={12} color="text.secondary" role="status">{aiStatus}</Typography></Box>
        <Stack spacing={3.5} role="log" aria-label="Conversa do atendimento" aria-live="polite" aria-relevant="additions">
          <Assistente><Typography fontSize={15}>Envie os documentos da compra e venda.</Typography><Typography fontSize={14} color="text.secondary" sx={{ mt: 1 }}>{assistida ? 'Depois, clique em Preparar minuta para abrir o texto e revisar os trechos que pedem sua atenção.' : 'Confira as fontes para preparar a minuta.'}</Typography></Assistente>
          {files.isLoading && <Typography fontSize={13} color="text.secondary">Consultando os documentos recebidos…</Typography>}
          {files.isError && <Alert severity="error" action={<Button onClick={() => files.refetch()}>Tentar novamente</Button>}>Não consegui consultar os anexos. Isso não significa que nenhum arquivo foi recebido.</Alert>}
          {!!files.data?.length && <>
            <Box sx={{ alignSelf: 'flex-end', maxWidth: { xs: '94%', sm: '82%' }, bgcolor: '#edf1e7', borderRadius: '16px 16px 4px 16px', p: 2 }}>
              <Typography fontSize={11} color="text.secondary" sx={{ mb: 1 }}>Documentos recebidos neste atendimento</Typography>
              <Stack spacing={1}>{files.data.map(file => <Stack key={file.id} direction="row" alignItems="center" gap={1}><FileText size={16} style={{ flexShrink: 0 }} />{assistida ? <Button size="small" sx={{ textAlign: 'left', overflowWrap: 'anywhere', minWidth: 0 }} onClick={() => setTools({ token: crypto.randomUUID(), acao: usaGpt && (!file.organizacao?.leitura_atual || file.organizacao.finalidade === 'pendente') ? 'organizacao' : 'leitura', anexo_id: file.id, leitura_versao: file.leitura_versao })}>{file.nome}</Button> : <Typography fontSize={13} sx={{ overflowWrap: 'anywhere' }}>{file.nome}</Typography>}</Stack>)}</Stack>
            </Box>
            {!assistida && <Assistente>
              <Typography fontSize={14}>Há {report.total} documento(s) salvo(s). Fiz apenas a extração local de texto, sem análise por IA.</Typography>
              {!!report.semTexto.length && <Alert severity="warning" sx={{ mt: 1.5 }}>Não encontrei texto extraível em: {report.semTexto.map(f => f.nome).join(', ')}. Confira o original e, se necessário, envie uma cópia mais legível.</Alert>}
              {!!report.incertos.length && <Typography fontSize={14} sx={{ mt: 1.5 }}>Preciso que você confira a leitura de: <strong>{report.incertos.map(f => f.nome).join(', ')}</strong>. Há páginas, trechos ou limites de leitura que não permitem tratar esses arquivos como integralmente lidos.</Typography>}
              {(comparison.isFetching || uploading) ? <Typography fontSize={13} role="status" sx={{ mt: 2 }}>Comparando os trechos dos anexos.</Typography>
                : comparison.isError ? <Alert severity="error" sx={{ mt: 2 }} action={<Button onClick={() => comparison.refetch()}>Tentar novamente</Button>}>Não foi possível comparar os anexos.</Alert>
                  : comparison.data && <ConferenciaAnexosChat report={comparison.data} onSource={source => setTools({
                    token: crypto.randomUUID(), acao: 'leitura', anexo_id: source.anexo_id,
                    pagina_id: source.pagina_id, leitura_versao: source.leitura_versao,
                  })} />}
              {!!readingQuestions.length && <Stack spacing={1.5} sx={{ mt: 2 }}>
                <Typography fontSize={14} fontWeight={650}>Vamos conferir a leitura?</Typography>
                {readingQuestions.map(question => <Box key={question.chave} sx={{ border: '1px solid #d5dfcd', borderRadius: 2, p: 1.5 }}>
                  <Typography fontSize={13} fontWeight={650} sx={{ overflowWrap: 'anywhere' }}>{question.arquivo}{question.pagina ? ` · página ${question.pagina}` : ' · arquivo incompleto'}</Typography>
                  <Typography fontSize={13} sx={{ mt: 1 }}>{question.motivo}</Typography>
                  {question.aviso && <Typography fontSize={12} color="text.secondary" sx={{ mt: 1 }}>{question.aviso}</Typography>}
                  {question.texto && <Box component="details" sx={{ mt: 1, fontSize: 13 }}><Box component="summary" sx={{ cursor: 'pointer', color: '#254c40' }}>Ver transcrição para conferir</Box><Typography component="pre" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontFamily: 'inherit', fontSize: 13, maxHeight: 260, overflow: 'auto' }}>{question.texto}</Typography></Box>}
                  <Button size="small" disabled={busy || !compose.ready || !!compose.value.texto.trim()} sx={{ mt: 1 }} onClick={() => compose.save({ texto: `Conferência de leitura: ${question.arquivo}${question.pagina ? `, página ${question.pagina}` : ''}. Leitura versão ${files.data?.find(f => f.nome === question.arquivo)?.leitura_versao}.\nAo comparar com o original, observei: `, client_id: '', texto_tentado: '' })}>Responder sobre esta leitura</Button>
                </Box>)}
                <Typography fontSize={12} color="text.secondary">Sua resposta fica registrada na conversa. A página continua pendente até a revisão manual; nenhum dado é confirmado automaticamente.</Typography>
              </Stack>}
              {hasText && <Button variant="outlined" startIcon={<Download size={15} />} sx={{ mt: 2, textAlign: 'left', fontSize: 12 }} onClick={() => txt('leitura-dos-documentos.txt', textoDosDocumentos(files.data || []))}>Abrir texto lido · TXT</Button>}
              <Button size="small" onClick={() => setTools(true)} sx={{ mt: 1 }}>Conferir originais e fontes</Button>
            </Assistente>}
            {assistida && !!report.semTexto.length && <Alert severity="warning">Confira a qualidade da imagem em {report.semTexto.map(file => file.nome).join(', ')}.</Alert>}
          </>}
          {messages.isError && <Alert severity="error" action={<Button onClick={() => messages.refetch()}>Tentar novamente</Button>}>Não foi possível carregar as mensagens salvas.</Alert>}
          {messages.data?.map(message => <Box key={message.id} sx={{ alignSelf: 'flex-end', maxWidth: { xs: '94%', sm: '82%' }, bgcolor: '#e9efe2', borderRadius: '16px 16px 4px 16px', p: 2 }}><Typography sx={{ fontSize: 14, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{message.texto}</Typography>{message.correcao_de && <Typography fontSize={11} color="text.secondary" sx={{ mt: .5 }}>Correção de uma informação anterior; histórico preservado.</Typography>}<Typography sx={{ color: '#788571', fontSize: 10, mt: .75 }}>{new Date(message.created_at).toLocaleString('pt-BR')}</Typography></Box>)}
          {ai.data?.respostas.map(answer => <Assistente key={answer.id}><Typography fontSize={11} color="text.secondary" sx={{ mb: 1 }}>Resposta à mensagem de {new Date(messages.data?.find(m => m.id === answer.mensagem_id)?.created_at || answer.created_at).toLocaleString('pt-BR')} · {answer.estado === 'concluido' ? 'GPT-6 Luna' : 'Status da análise'}</Typography><Typography fontSize={14} sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{answer.estado === 'processando' ? 'A resposta ainda está sendo processada ou não foi confirmada. Atualize as respostas para consultar; não envie a mesma solicitação novamente.' : answer.texto}</Typography></Assistente>)}
          {answerUnconfirmed && <Alert severity="warning">Sua mensagem foi salva. A resposta da IA ainda não foi confirmada.</Alert>}
          {(ai.isError || answerUnconfirmed || !!ai.data?.respostas.length) && <Button size="small" disabled={ai.isFetching} onClick={() => ai.refetch()}>Atualizar respostas · sem nova análise</Button>}
          {!assistida && ai.isSuccess && !ai.data.habilitado && !!messages.data?.length && <Assistente><Typography fontSize={14}>Sua informação está salva na conversa. Ela ainda não confirma um dado nem resolve automaticamente uma divergência. A interpretação por IA está desativada.</Typography></Assistente>}
          {draft.isLoading && <Typography fontSize={13} color="text.secondary" role="status">Consultando as minutas salvas…</Typography>}
          {draft.isError && <Alert severity="error" action={<Button onClick={() => draft.refetch()}>Tentar novamente</Button>}>Não foi possível consultar as minutas salvas.</Alert>}
          {current && <Assistente>
            <Box component="section" aria-label="Minuta de compra e venda" sx={{ bgcolor: 'background.paper', border: 1, borderColor: 'divider', borderRadius: 2, p: 2 }}>
              <Typography component="h2" variant="subtitle1" fontWeight={650}>Minuta de compra e venda · Rascunho</Typography>
              <Typography variant="body2" color="text.secondary">Versão {current.versao} · Modelo v{current.modelo_versao}</Typography>
              <Button variant="outlined" startIcon={<FileText size={16} />} sx={{ mt: 1.5 }} onClick={() => setMinutaAberta(current)}>Abrir minuta</Button>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {current.desatualizada ? 'O atendimento mudou. Prepare uma nova versão e compare com o texto salvo.' : current.assistencia ? 'Confira o texto e os trechos sinalizados no editor.' : current.tipo === 'editada' ? 'Versão salva com edição manual. Confira as alterações antes de registrar a revisão.' : 'Rascunho preparado com o modelo aprovado e os dados conferidos.'}
            </Typography>
            <FontesDaMinutaChat minuta={current} onSource={source => setTools({ ...source, token: crypto.randomUUID(), acao: 'leitura' })} />
            {current.desatualizada && affected.length > 0 && <Stack spacing={.75} sx={{ mt: 1.5 }}>
              <Typography variant="body2">Trechos que pedem conferência na v{current.versao}</Typography>
              <Typography variant="body2" color="text.secondary">{affected.map(question => question.rotulo).join(' · ')}</Typography>
              <Button size="small" sx={{ alignSelf: 'flex-start' }} onClick={() => setAjuste({ campos: [], pessoaIndefinida: false, texto: 'Conferir os campos afetados pelos documentos', minuta: current })}>Revisar ajustes dos anexos</Button>
            </Stack>}
          </Assistente>}
          {ajuste && <Assistente>
            {conference.isLoading ? <Typography role="status" variant="body2">Consultando os trechos e as pendências…</Typography>
              : conference.isError && !conference.data ? <Alert severity="error" action={<Button onClick={() => conference.refetch()}>Tentar novamente</Button>}>Não foi possível consultar as fontes.</Alert>
                : <AjusteMinutaChat key={`${ajuste.minuta.id}:${ajuste.texto}`} id={id} minuta={ajuste.minuta} pedido={ajuste} perguntas={conference.data?.pendencias || []}
                  onSaved={async () => { await Promise.all(['mensagens-atendimento', 'conferencia-atendimento', 'ficha-atendimento', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] }))) }}
                  onSource={source => setTools({ ...source, token: crypto.randomUUID(), acao: 'leitura' })} onClose={() => setAjuste(null)} />}
          </Assistente>}
          {draft.isSuccess && (!current || current.desatualizada || (!assistida && !draft.data.pronto)) && <Assistente>
            {assistida ? <Typography fontSize={14}>{preparing ? 'Lendo os anexos e montando a minuta…' : usaGpt ? 'Em “Revisão e ajustes”, classifique os documentos e selecione as páginas que serão usadas.' : 'A minuta será preparada com os documentos deste atendimento.'}</Typography> : <>
              <Typography fontSize={14}>A minuta usa o modelo aprovado neste atendimento e os dados conferidos.</Typography>
              {!draft.data.modelo_aprovado && <Typography fontSize={13} sx={{ mt: 1 }}>Revise e aprove o modelo em “Revisão e ajustes” para preparar a minuta.</Typography>}
              {!!draft.data.pendencias && <Typography fontSize={13} sx={{ mt: 1 }}>Há {draft.data.pendencias} pendência(s) para conferir.</Typography>}
              {draft.data.motivo_bloqueio && !draft.data.pronto && <Typography fontSize={13} color="text.secondary" sx={{ mt: 1 }}>{draft.data.motivo_bloqueio}</Typography>}
            </>}
            <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1.5 }}>
              <Button variant="contained" startIcon={<FileText size={16} />} disabled={busy || (assistida ? !arquivosDoCaso.length : !draft.data.pronto || !draft.data.modelo_aprovado)} onClick={() => void prepararMinuta()}>{preparing ? 'Preparando…' : current ? 'Preparar nova versão' : 'Preparar minuta'}</Button>
              {!assistida && <Button onClick={() => setTools(true)}>Conferir modelo e pendências</Button>}
            </Stack>
          </Assistente>}
          <div ref={end} />
        </Stack>
        <Box component="form" onSubmit={send} sx={{ position: 'sticky', bottom: 0, bgcolor: '#f7f7f2', pt: 2.5, pb: 'max(12px, env(safe-area-inset-bottom))', mt: 2, zIndex: 2 }}>
          {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
          {compose.aviso && <Alert severity="warning" sx={{ mb: 1 }}>{compose.aviso}</Alert>}
          {!!progress && <Stack direction="row" gap={1} sx={{ mb: 1 }} role="status"><CircularProgress size={15} /><Typography fontSize={12} sx={{ overflowWrap: 'anywhere' }}>{progress}</Typography></Stack>}
          <Stack direction="row" alignItems="flex-end" gap={.5} sx={{ p: 1, border: '1px solid #d5dfcd', bgcolor: '#fff', borderRadius: '18px', boxShadow: '0 4px 20px #254c4008' }}>
            <IconButton aria-label="Anexar documentos" disabled={busy || !files.isSuccess} onClick={() => input.current?.click()}><Paperclip size={20} /></IconButton>
            <input ref={input} type="file" hidden multiple accept=".pdf,.txt,.png,.jpg,.jpeg" onChange={event => { void upload(event.target.files); event.target.value = '' }} />
            <TextField multiline minRows={1} maxRows={6} fullWidth placeholder="Escreva sobre este atendimento…" value={compose.value.texto} onChange={e => compose.save(old => ({ ...old, texto: e.target.value }))} disabled={busy} variant="standard" slotProps={{ htmlInput: { maxLength: 10000, 'aria-label': 'Mensagem do atendimento' }, input: { disableUnderline: true } }} sx={{ '& .MuiInputBase-input': { p: '9px 7px', fontSize: 14 } }} />
            <IconButton type="submit" aria-label="Enviar mensagem" disabled={busy || !compose.ready || !compose.value.texto.trim() || !messages.isSuccess} sx={{ bgcolor: '#254c40', color: '#fff', '&:hover': { bgcolor: '#193c30' }, '&.Mui-disabled': { bgcolor: '#eef1e9' } }}>{sending ? <CircularProgress size={19} color="inherit" /> : <ArrowUp size={19} />}</IconButton>
          </Stack>
          <Typography sx={{ textAlign: 'center', fontSize: 10, color: '#7a8575', mt: 1 }}>Anexar não confirma dados. Mensagens ficam salvas ao enviar.</Typography>
        </Box>
      </>}
    </Stack>
    {minutaAberta && <EditorMinuta key={scope.join(":")} id={id} scope={scope} inicial={minutaAberta} onClose={() => setMinutaAberta(null)} />}
    <Dialog open={!!tools} onClose={closeTools} fullWidth maxWidth="lg" aria-labelledby="revisao-ajustes-title"><DialogTitle id="revisao-ajustes-title" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>Revisão e ajustes<IconButton aria-label="Fechar revisão" onClick={closeTools}><X size={19} /></IconButton></DialogTitle><DialogContent>{tools && <FerramentasDoAtendimento key={scope.join(':')} id={id} documentoInicial={tools === true ? null : tools} />}</DialogContent></Dialog>
  </AtendimentoLayout>
}
