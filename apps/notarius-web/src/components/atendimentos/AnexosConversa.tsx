'use client'

import { useEffect, useRef, useState } from 'react'
import { descreverLimites } from '@/lib/limitesLeitura'
import { propostasDadosApi } from '@/lib/propostasDados'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type Anexo, type FonteDocumento, type PedidoDocumento } from '@/lib/atendimentos'
import { PaginaLeitura } from './PaginaLeitura'
import { fichaDetalhadaApi } from '@/lib/fichaDetalhada'
import { OrganizarAnexo, finalidadesDocumento, nomeDestinatario } from './OrganizarAnexo'

export function AnexosConversa({ id, scope, onSource, pedido, onPedidoConsumido }: { id: string; scope: (string | undefined)[]; onSource: (source: FonteDocumento) => void; pedido?: PedidoDocumento | null; onPedidoConsumido?: () => void }) {
  const cache = useQueryClient()
  const key = ['anexos-atendimento', ...scope]
  const query = useQuery({ queryKey: key, queryFn: () => atendimentosApi.anexos(id) })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState<Anexo | null>(null)
  const [notice, setNotice] = useState('')
  const [organizing, setOrganizing] = useState<string | null>(null)
  const [purposeFilter, setPurposeFilter] = useState('todos'), [typeFilter, setTypeFilter] = useState('todos'), [ownerFilter, setOwnerFilter] = useState('todos')
  const sheet = useQuery({ queryKey: ['ficha-detalhada', ...scope], queryFn: () => fichaDetalhadaApi.get(id) })
  const objects = (sheet.data?.objetos || []).filter(o => ['pessoa', 'imovel'].includes(o.tipo))
  const organizingFile = query.data?.find(a => a.id === organizing)
  const visible = (query.data || []).filter(a => (purposeFilter === 'todos' || (a.organizacao?.finalidade || 'pendente') === purposeFilter) && (typeFilter === 'todos' || a.organizacao?.tipo_documento === typeFilter) && (ownerFilter === 'todos' || a.organizacao?.vinculos.some(v => (v.objeto_id || 'atendimento') === ownerFilter)))
  const currentDetail = query.data?.find(a => a.id === detail?.id)
  const openedRequest = useRef('')
  useEffect(() => {
    if (!pedido || pedido.token === openedRequest.current) return
    const file = query.data?.find(a => a.id === pedido.anexo_id)
    if (!file) return
    openedRequest.current = pedido.token
    if (pedido.acao === 'organizacao') setOrganizing(file.id)
    else {
      setDetail(file)
      if (pedido.pagina_id) requestAnimationFrame(() => document.getElementById(`pagina-leitura-${pedido.pagina_id}`)?.scrollIntoView({ block: 'center' }))
    }
    onPedidoConsumido?.()
  }, [pedido, query.data, onPedidoConsumido])
  const proposalRetry = useRef<{ key: string; id: string } | null>(null)
  async function extract(item: Anexo) {
    const sourceKey = `${item.id}:${item.leitura_versao}`
    if (proposalRetry.current?.key !== sourceKey) proposalRetry.current = { key: sourceKey, id: crypto.randomUUID() }
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await propostasDadosApi.extrair(id, { anexo_id: item.id, leitura_versao: item.leitura_versao }, proposalRetry.current.id)
      setNotice(`${result.propostas_ids.length} proposta(s) localizadas; ${result.linhas_nao_interpretadas} linha(s) não interpretadas. ${result.problemas_leitura.join(' ')} Revise na Conversa → Ficha detalhada → Propostas com fonte. ${result.aviso}`)
      await Promise.all(['ficha-detalhada', 'propostas-dados', 'conferencia-atendimento', 'minuta-atendimento'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      proposalRetry.current = null
    } catch { setError('Não foi possível registrar as propostas locais. Confira a versão da leitura e tente novamente. Nenhum dado foi confirmado.') }
    finally { setBusy(false) }
  }
  async function upload(file: File) {
    setError('')
    if (file.size > 10 * 1024 * 1024) { setError('O limite por arquivo é de 10 MB.'); return }
    setBusy(true)
    try {
      const saved = await atendimentosApi.upload(id, file)
      await cache.invalidateQueries({ queryKey: key })
      await cache.invalidateQueries({ queryKey: ['conferencia-atendimento'] })
      await cache.invalidateQueries({ queryKey: ['minuta-atendimento'] })
      if (saved.situacao === 'revisao') setDetail(saved)
    } catch (err) {
      const message = (err as { response?: { data?: unknown } }).response?.data
      setError(typeof message === 'string' ? message : Array.isArray(message) ? message.join(' ') : 'Não foi possível concluir o envio. Atualize os anexos antes de tentar novamente.')
    } finally { setBusy(false) }
  }
  async function download(item: Anexo) {
    try {
      const blob = await atendimentosApi.download(id, item.id)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = item.nome; anchor.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch { setError('Não foi possível baixar o original.') }
  }
  async function reread(item: Anexo) {
    setBusy(true); setError('')
    try {
      const saved = await atendimentosApi.relerAnexo(id, item.id, item.leitura_versao)
      await Promise.all([
        cache.invalidateQueries({ queryKey: key }),
        cache.invalidateQueries({ queryKey: ['conferencia-atendimento'] }),
        cache.invalidateQueries({ queryKey: ['minuta-atendimento'] }),
        cache.invalidateQueries({ queryKey: ['ficha-atendimento'] }),
        cache.invalidateQueries({ queryKey: ['ficha-detalhada'] }),
        cache.invalidateQueries({ queryKey: ['propostas-dados'] }),
      ])
      setDetail(saved)
    } catch { setError('Não consegui confirmar a nova leitura. Atualize os anexos antes de tentar novamente.') }
    finally { setBusy(false) }
  }
  return <Stack spacing={2}>
    {organizingFile && <OrganizarAnexo key={`${scope.join(':')}:${organizingFile.id}`} id={id} scope={scope} anexo={organizingFile} objetos={objects} onClose={() => setOrganizing(null)} />}
    <Box id="anexar-arquivo"><Button component="label" variant="contained" disableElevation disabled={busy}>{busy ? 'Recebendo e lendo…' : 'Enviar documento'}
      <input type="file" hidden accept=".pdf,.txt,.png,.jpg,.jpeg" disabled={busy} onChange={e => { const file = e.target.files?.[0]; e.target.value = ''; if (file) void upload(file) }} />
    </Button><Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>PDF, foto ou arquivo de texto · até 10 MB por arquivo.</Typography>
      <Box component="details" sx={{ mt: 1 }}><Box component="summary" sx={{ cursor: 'pointer', color: 'primary.main', py: 1 }}>Sobre a leitura dos arquivos</Box><Typography variant="body2" color="text.secondary">Aceita PDF, TXT, PNG e JPG. A leitura de imagens usa OCR local em português, em até 10 páginas digitalizadas por PDF. Sempre confira o resultado no original.</Typography></Box>
    </Box>
    {query.isLoading && <Typography>Carregando documentos…</Typography>}
    {query.isSuccess && !query.data.length && <Box sx={{ p: 3, bgcolor: '#f5f8fc', borderRadius: 2 }}><Typography fontWeight={600}>Nenhum documento enviado</Typography><Typography color="text.secondary">Use o botão acima para enviar o primeiro arquivo deste atendimento.</Typography></Box>}
    {error && <Alert severity="error">{error}</Alert>}
    {notice && <Alert severity="info">{notice}</Alert>}
    <Alert severity="info">Análise automática por IA indisponível neste piloto. Para continuar manualmente: confira o original e a leitura, classifique a quem o documento pertence e abra Conversa → Ficha detalhada. Escolha a pessoa ou o imóvel e o campo; selecione a página como fonte, transcreva o trecho e revise o valor. Informação expressa da escrevente também pode ser registrada, preservando uma mensagem de origem. Nada é confirmado ao enviar o arquivo.</Alert>
    <Typography variant="body2" color="text.secondary">A extração por rótulos abaixo é local e limitada; não interpreta livremente documentos. O provedor simulado existe somente nos testes.</Typography>
    {sheet.isLoading && <Typography role="status">Consultando pessoas e imóveis para mostrar os destinatários e permitir a classificação…</Typography>}
    {!!query.data?.length && <Stack spacing={1} direction={{ xs: 'column', md: 'row' }}>
      <TextField select label="Finalidade" value={purposeFilter} onChange={e => setPurposeFilter(e.target.value)} fullWidth><MenuItem value="todos">Todos os arquivos</MenuItem>{Object.entries(finalidadesDocumento).map(([v, label]) => <MenuItem key={v} value={v}>{label}</MenuItem>)}</TextField>
      <TextField select label="Tipo" value={typeFilter} onChange={e => setTypeFilter(e.target.value)} fullWidth><MenuItem value="todos">Todos os tipos</MenuItem>{[...new Set(query.data.map(a => a.organizacao?.tipo_documento).filter((v): v is string => !!v))].map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}</TextField>
      <TextField select label="Destinatário" value={ownerFilter} onChange={e => setOwnerFilter(e.target.value)} fullWidth><MenuItem value="todos">Todos os destinatários</MenuItem><MenuItem value="atendimento">Atendimento geral</MenuItem>{objects.map(o => <MenuItem key={o.id} value={o.id}>{nomeDestinatario(o)}</MenuItem>)}</TextField>
    </Stack>}
    {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Recarregar</Button>}>Não foi possível carregar os anexos.</Alert>}
    {query.isSuccess && visible.map(item => <Box key={item.id} sx={{ p: 2.5, border: '1px solid #dce4ee', borderRadius: 2 }}>
      <Typography fontWeight={600} sx={{ overflowWrap: 'anywhere' }}>📎 {item.nome}</Typography>
      <Typography variant="caption" color="text.secondary">Leitura v{item.leitura_versao}</Typography>
      <Typography>{item.organizacao?.tipo_documento || 'Tipo ainda não classificado'} · {finalidadesDocumento[item.organizacao?.finalidade || 'pendente']}</Typography>
      {item.organizacao?.vinculos.map((v, i) => <Typography key={i} variant="body2">{v.objeto_id ? objects.find(o => o.id === v.objeto_id) ? nomeDestinatario(objects.find(o => o.id === v.objeto_id)!) : `Registro ${v.objeto_id.slice(0, 8)}` : 'Atendimento geral'} · {v.paginas.length ? `páginas ${v.paginas.join(', ')}` : 'todas as páginas/unidades'}</Typography>)}
      <Button size="small" disabled={busy || sheet.isError || sheet.isLoading} onClick={() => setOrganizing(item.id)}>Classificar e vincular documento</Button>
      {item.organizacao?.finalidade === 'referencia_redacao' && <Alert severity="info">Referência de redação separada das fontes do caso. Nenhum dado deste exemplo deve preencher a compra e venda.</Alert>}
      {item.organizacao?.versao > 0 && !item.organizacao.leitura_atual && <Alert severity="warning">Confira a classificação e os destinatários novamente após a releitura.</Alert>}
      <Typography variant="body2" color={item.situacao === 'revisao' ? 'warning.main' : 'text.secondary'}>{item.situacao === 'revisao' ? 'Preciso da sua revisão para este arquivo.' : 'Texto disponível para conferir. A situação de cada dado está na ficha; a leitura do arquivo não confirma seus campos.'}</Typography>
      <Button size="small" onClick={() => setDetail(item)}>Conferir leitura</Button><Button size="small" onClick={() => download(item)}>Baixar original</Button>
      <Button size="small" disabled={busy || ['referencia_redacao', 'nao_utilizar'].includes(item.organizacao?.finalidade)} onClick={() => extract(item)}>Guardar propostas locais para revisão</Button>
      {item.mime !== 'text/plain' && <Button size="small" disabled={busy} onClick={() => reread(item)}>Ler novamente</Button>}
    </Box>)}
    {sheet.isError && <Alert severity="error">Não foi possível consultar as pessoas e imóveis da ficha. Atualize antes de classificar os destinatários.</Alert>}
    <Dialog open={!!currentDetail} onClose={() => setDetail(null)} fullWidth maxWidth="md"><DialogTitle sx={{ overflowWrap: 'anywhere' }}>{currentDetail?.nome}</DialogTitle>
      <DialogContent><Stack spacing={2}>
        <Alert severity={currentDetail?.situacao === 'revisao' ? 'warning' : 'info'}>{currentDetail?.aviso}</Alert>
        <Typography>Total de páginas/unidades informado: {currentDetail?.cobertura?.total_paginas ?? 'não identificado'} · processadas: {currentDetail?.cobertura?.paginas_processadas ?? currentDetail?.paginas.length}</Typography>
        {!!currentDetail?.cobertura?.paginas_sem_texto.length && <Alert severity="warning">Sem texto reconhecido: {currentDetail.cobertura.paginas_sem_texto.join(', ')}.</Alert>}
        {!!currentDetail?.cobertura?.paginas_incertas.length && <Alert severity="warning">Leitura parcial ou incerta: {currentDetail.cobertura.paginas_incertas.join(', ')}.</Alert>}
        {!!currentDetail?.cobertura?.limites?.length && <Alert severity="warning">Limites atingidos: {descreverLimites(currentDetail.cobertura.limites)}. Confira o original; a extração não cobriu integralmente o arquivo.</Alert>}
        <Typography variant="body2">Não preenchi nem confirmei campos automaticamente. Confira o original: a extração pode omitir texto, imagens e formatação.</Typography>
        <Typography variant="body2">Ausência de texto reconhecido não significa inexistência do fato. Classificar o documento não resolve falha de leitura nem confirma dados.</Typography>
        {currentDetail?.paginas.map(page => <Box key={page.id} id={`pagina-leitura-${page.id}`}><PaginaLeitura id={id} anexo={currentDetail} pagina={page} onSource={source => { onSource(source); setDetail(null) }} /></Box>)}
      </Stack></DialogContent><DialogActions><Button onClick={() => setDetail(null)}>Fechar leitura</Button></DialogActions>
    </Dialog>
  </Stack>
}
