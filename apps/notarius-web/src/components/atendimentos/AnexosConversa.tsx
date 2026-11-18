'use client'

import { useEffect, useRef, useState } from 'react'
import { descreverLimites } from '@/lib/limitesLeitura'
import { propostasDadosApi } from '@/lib/propostasDados'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { ChevronDown, Download, FileText, UploadCloud } from 'lucide-react'
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
  const requestedPage = useRef<string | undefined>(undefined)
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
    if (!pedido || pedido.token === openedRequest.current || query.isFetching) return
    const file = query.data?.find(a => a.id === pedido.anexo_id)
    if (!file) return
    openedRequest.current = pedido.token
    if (pedido.leitura_versao !== undefined && pedido.leitura_versao !== file.leitura_versao) {
      setError('A leitura deste documento mudou. Feche a revisão para atualizar a comparação e confira a fonte novamente.')
    } else if (pedido.acao === 'organizacao') setOrganizing(file.id)
    else {
      requestedPage.current = pedido.pagina_id
      setDetail(file)
    }
    onPedidoConsumido?.()
  }, [pedido, query.data, query.isFetching, onPedidoConsumido])
  const proposalRetry = useRef<{ key: string; id: string } | null>(null)
  async function extract(item: Anexo) {
    const sourceKey = `${item.id}:${item.leitura_versao}`
    if (proposalRetry.current?.key !== sourceKey) proposalRetry.current = { key: sourceKey, id: crypto.randomUUID() }
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await propostasDadosApi.extrair(id, { anexo_id: item.id, leitura_versao: item.leitura_versao }, proposalRetry.current.id)
      setNotice(`${result.propostas_ids.length} proposta(s) localizadas; ${result.linhas_nao_interpretadas} linha(s) não interpretadas. ${result.problemas_leitura.join(' ')} Revise em Dados do caso → Abrir ficha do caso → Propostas com fonte. ${result.aviso}`)
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
    <Box id="anexar-arquivo" sx={{ p: { xs: 2.5, sm: 3 }, border: '1.5px dashed #bccdbd', borderRadius: 3, bgcolor: '#f7faf4' }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} gap={2.5} alignItems={{ xs: 'flex-start', sm: 'center' }}>
        <Box sx={{ width: 50, height: 50, borderRadius: 3, bgcolor: '#e5eedc', color: '#254c40', display: 'grid', placeItems: 'center', flexShrink: 0 }}><UploadCloud size={25} strokeWidth={1.5} aria-hidden="true" /></Box>
        <Box sx={{ flex: 1 }}><Typography component="h3" fontWeight={650} sx={{ color: '#203c35', fontSize: 17 }}>Adicione os documentos do caso</Typography><Typography variant="body2" color="text.secondary" sx={{ mt: .5 }}>PDF, foto ou texto. Até 10 MB por arquivo.</Typography></Box>
        <Button component="label" variant="contained" disableElevation disabled={busy} startIcon={<UploadCloud size={17} />} sx={{ flexShrink: 0 }}>{busy ? 'Recebendo e lendo…' : 'Enviar documento'}
          <input type="file" hidden accept=".pdf,.txt,.png,.jpg,.jpeg" disabled={busy} onChange={e => { const file = e.target.files?.[0]; e.target.value = ''; if (file) void upload(file) }} />
        </Button>
      </Stack>
    </Box>
    <Box>
      <Typography variant="body2" color="text.secondary">Confira o original, identifique a quem pertence e use a ficha para registrar os dados.</Typography>
      <Box component="details" sx={{ mt: .5, '&[open] summary': { mb: 1 }, '& summary::marker': { color: '#7a8d79' } }}><Box component="summary" sx={{ cursor: 'pointer', color: 'primary.main', py: .75, fontSize: 13, fontWeight: 600 }}>Como conferir e registrar os dados</Box>
        <Stack spacing={1} sx={{ p: 2, borderRadius: 2, border: '1px solid #e3e8e1', bgcolor: '#fafbf8' }}>
          <Typography variant="body2" color="text.secondary">Para corrigir dados na ficha, confira a leitura e classifique o documento. Em Dados do caso → Abrir ficha do caso, escolha a pessoa ou o imóvel, indique o campo e a página de origem e registre o valor conferido.</Typography>
          <Typography variant="body2" color="text.secondary">Uma informação expressa da escrevente pode ser registrada com uma mensagem de origem. As propostas locais por rótulos são limitadas e também exigem revisão; não interpretam livremente o documento.</Typography>
          <Typography variant="body2" color="text.secondary">Formatos aceitos: PDF, TXT, PNG e JPG. Imagens usam OCR local em português, em até 10 páginas digitalizadas por PDF. Confira o original mesmo quando houver texto reconhecido.</Typography>
        </Stack>
      </Box>
    </Box>
    {query.isLoading && <Typography>Carregando documentos…</Typography>}
    {query.isSuccess && !query.data.length && <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>Os documentos enviados aparecerão aqui.</Typography>}
    {error && <Alert severity="error">{error}</Alert>}
    {notice && <Alert severity="info">{notice}</Alert>}
    {sheet.isLoading && <Typography role="status">Consultando pessoas e imóveis para mostrar os destinatários e permitir a classificação…</Typography>}
    {!!query.data?.length && <Stack spacing={1} direction={{ xs: 'column', md: 'row' }}>
      <TextField select label="Finalidade" value={purposeFilter} onChange={e => setPurposeFilter(e.target.value)} fullWidth><MenuItem value="todos">Todos os arquivos</MenuItem>{Object.entries(finalidadesDocumento).map(([v, label]) => <MenuItem key={v} value={v}>{label}</MenuItem>)}</TextField>
      <TextField select label="Tipo" value={typeFilter} onChange={e => setTypeFilter(e.target.value)} fullWidth><MenuItem value="todos">Todos os tipos</MenuItem>{[...new Set(query.data.map(a => a.organizacao?.tipo_documento).filter((v): v is string => !!v))].map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}</TextField>
      <TextField select label="Destinatário" value={ownerFilter} onChange={e => setOwnerFilter(e.target.value)} fullWidth><MenuItem value="todos">Todos os destinatários</MenuItem><MenuItem value="atendimento">Atendimento geral</MenuItem>{objects.map(o => <MenuItem key={o.id} value={o.id}>{nomeDestinatario(o)}</MenuItem>)}</TextField>
    </Stack>}
    {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Recarregar</Button>}>Não foi possível carregar os anexos.</Alert>}
    {query.isSuccess && !!query.data.length && !visible.length && <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>Nenhum documento corresponde aos filtros.</Typography>}
    {query.isSuccess && visible.map(item => <Box key={item.id} sx={{ p: { xs: 2, sm: 2.5 }, border: '1px solid #e3e8e1', borderRadius: 3, bgcolor: '#fff' }}>
      <Stack direction="row" alignItems="flex-start" gap={1.5} sx={{ mb: 1.5 }}>
        <Box sx={{ width: 40, height: 44, bgcolor: '#f0f4eb', border: '1px solid #e4eadf', borderRadius: 2, color: '#496349', display: 'grid', placeItems: 'center', flexShrink: 0 }}><FileText size={21} strokeWidth={1.5} aria-hidden="true" /></Box>
        <Box sx={{ minWidth: 0, flex: 1 }}><Typography fontWeight={650} sx={{ overflowWrap: 'anywhere', color: '#203c35' }}>{item.nome}</Typography><Typography variant="caption" color="text.secondary">{item.organizacao?.tipo_documento || 'Sem classificação'} · leitura v{item.leitura_versao}</Typography></Box>
        <Chip size="small" variant="outlined" label={item.situacao === 'revisao' ? 'Revisar leitura' : 'Leitura disponível'} sx={{ display: { xs: 'none', sm: 'inline-flex' }, color: item.situacao === 'revisao' ? '#8a642a' : '#496349', borderColor: item.situacao === 'revisao' ? '#e6d7bb' : '#d5e2cc', fontSize: 12 }} />
      </Stack>
      <Stack spacing={.5} sx={{ mb: 1.5 }}>
        <Typography variant="body2" color="text.secondary">{finalidadesDocumento[item.organizacao?.finalidade || 'pendente']}</Typography>
        {item.organizacao?.vinculos.map((v, i) => <Typography key={i} variant="body2" color="text.secondary">{v.objeto_id ? objects.find(o => o.id === v.objeto_id) ? nomeDestinatario(objects.find(o => o.id === v.objeto_id)!) : `Registro ${v.objeto_id.slice(0, 8)}` : 'Atendimento geral'} · {v.paginas.length ? `páginas ${v.paginas.join(', ')}` : 'documento inteiro'}</Typography>)}
      </Stack>
      {item.organizacao?.finalidade === 'referencia_redacao' && <Alert severity="info">Referência de redação separada das fontes do caso. Nenhum dado deste exemplo deve preencher a compra e venda.</Alert>}
      {item.organizacao?.versao > 0 && !item.organizacao.leitura_atual && <Alert severity="warning">Confira a classificação e os destinatários novamente após a releitura.</Alert>}
      <Typography variant="body2" color={item.situacao === 'revisao' ? 'warning.main' : 'text.secondary'} sx={{ mb: 1.5 }}>{item.situacao === 'revisao' ? 'Confira este arquivo: a leitura precisa de revisão.' : 'Texto disponível. Os dados ainda precisam ser conferidos na ficha.'}</Typography>
      <Stack direction="row" gap={1} flexWrap="wrap"><Button size="small" variant="outlined" onClick={() => setDetail(item)}>Conferir leitura</Button><Button size="small" disabled={busy || sheet.isError || sheet.isLoading} onClick={() => setOrganizing(item.id)}>Identificar documento</Button><Button size="small" startIcon={<Download size={15} />} onClick={() => download(item)}>Original</Button></Stack>
      <Box component="details" sx={{ mt: 1 }}><Box component="summary" sx={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: .5, color: 'text.secondary', fontSize: 12, py: .75, width: 'fit-content' }}>Outras ações <ChevronDown size={14} aria-hidden="true" /></Box><Stack spacing={.5} alignItems="flex-start" sx={{ pt: .5 }}>
        <Typography variant="caption" color="text.secondary">A extração local reconhece apenas alguns rótulos. Nenhuma proposta confirma os dados.</Typography>
        <Button size="small" disabled={busy || ['referencia_redacao', 'nao_utilizar'].includes(item.organizacao?.finalidade)} onClick={() => extract(item)}>Buscar propostas por rótulos</Button>
        {item.mime !== 'text/plain' && <Button size="small" disabled={busy} onClick={() => reread(item)}>Refazer leitura do arquivo</Button>}
      </Stack></Box>
    </Box>)}
    {sheet.isError && <Alert severity="error">Não foi possível consultar as pessoas e imóveis da ficha. Atualize antes de classificar os destinatários.</Alert>}
    <Dialog open={!!currentDetail} onClose={() => setDetail(null)} fullWidth maxWidth="md" slotProps={{ transition: { onEntered: () => {
      if (!requestedPage.current) return
      const page = document.getElementById(`pagina-leitura-${requestedPage.current}`)
      requestedPage.current = undefined
      page?.scrollIntoView({ block: 'start' })
      page?.focus({ preventScroll: true })
    } } }}><DialogTitle sx={{ overflowWrap: 'anywhere' }}>{currentDetail?.nome}</DialogTitle>
      <DialogContent><Stack spacing={2}>
        <Alert severity={currentDetail?.situacao === 'revisao' ? 'warning' : 'info'}>{currentDetail?.aviso}</Alert>
        <Typography>Total de páginas/unidades informado: {currentDetail?.cobertura?.total_paginas ?? 'não identificado'} · processadas: {currentDetail?.cobertura?.paginas_processadas ?? currentDetail?.paginas.length}</Typography>
        {!!currentDetail?.cobertura?.paginas_sem_texto.length && <Alert severity="warning">Sem texto reconhecido: {currentDetail.cobertura.paginas_sem_texto.join(', ')}.</Alert>}
        {!!currentDetail?.cobertura?.paginas_incertas.length && <Alert severity="warning">Leitura parcial ou incerta: {currentDetail.cobertura.paginas_incertas.join(', ')}.</Alert>}
        {!!currentDetail?.cobertura?.limites?.length && <Alert severity="warning">Limites atingidos: {descreverLimites(currentDetail.cobertura.limites)}. Confira o original; a extração não cobriu integralmente o arquivo.</Alert>}
        <Typography variant="body2">Não preenchi nem confirmei campos automaticamente. Confira o original: a extração pode omitir texto, imagens e formatação.</Typography>
        <Typography variant="body2">Ausência de texto reconhecido não significa inexistência do fato. Classificar o documento não resolve falha de leitura nem confirma dados.</Typography>
        {currentDetail?.paginas.map(page => <Box key={page.id} id={`pagina-leitura-${page.id}`} tabIndex={-1}><PaginaLeitura id={id} anexo={currentDetail} pagina={page} onSource={source => { onSource(source); setDetail(null) }} /></Box>)}
      </Stack></DialogContent><DialogActions><Button onClick={() => setDetail(null)}>Fechar leitura</Button></DialogActions>
    </Dialog>
  </Stack>
}
