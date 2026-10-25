'use client'
import { useEffect, useState } from 'react'
import Image from 'next/image'
import { descreverLimites } from '@/lib/limitesLeitura'
import { Alert, Box, Button, Stack, Typography } from '@mui/material'
import { atendimentosApi, type Anexo, type FonteDocumento, type PaginaAnexo } from '@/lib/atendimentos'

export function PaginaLeitura({ id, anexo, pagina, onSource }: { id: string; anexo: Anexo; pagina: PaginaAnexo; onSource: (source: FonteDocumento) => void }) {
  const [showImage, setShowImage] = useState(false)
  const [imageUrl, setImageUrl] = useState('')
  const [imageError, setImageError] = useState('')
  const [region, setRegion] = useState<number | null>(null)
  useEffect(() => {
    if (!showImage) return
    let cancelled = false
    let url = ''
    setImageError('')
    atendimentosApi.imagemPagina(id, anexo.id, pagina.id).then(blob => {
      url = URL.createObjectURL(blob)
      if (cancelled) URL.revokeObjectURL(url)
      else setImageUrl(url)
    }).catch(() => { if (!cancelled) setImageError('Não consegui exibir a página. Baixe o original para conferir.') })
    return () => { cancelled = true; if (url) URL.revokeObjectURL(url) }
  }, [showImage, id, anexo.id, pagina.id])
  function selectSource(text: string, canal: 'texto' | 'ocr') {
    if (['referencia_redacao', 'nao_utilizar'].includes(anexo.organizacao?.finalidade || 'pendente')) return
    onSource({ organizacao_versao: anexo.organizacao?.versao ?? 0, pagina_id: pagina.id, arquivo: anexo.nome, pagina: pagina.numero, trecho: text.slice(0, 10000), canal })
  }
  const box = region !== null ? pagina.regioes_ocr[region] : null
  const textStyle = { whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontFamily: 'inherit', maxHeight: 300, overflow: 'auto', p: 1, bgcolor: 'action.hover' }
  return <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 2 }}>
    <Typography variant="h6">{anexo.mime === 'text/plain' ? 'Texto do arquivo' : `Página ${pagina.numero}`}</Typography>
    {!!pagina.limites_leitura?.length && <Alert severity="warning">Limites atingidos: {descreverLimites(pagina.limites_leitura)}. A página não foi integralmente coberta; confira o original.</Alert>}
    <Alert severity={pagina.situacao === 'revisao' ? 'warning' : 'info'} sx={{ my: 1 }}>{pagina.aviso}</Alert>
    {anexo.mime !== 'text/plain' && <Button onClick={() => setShowImage(!showImage)}>{showImage ? 'Ocultar página' : 'Ver página para conferir'}</Button>}
    {showImage && <>
      {!imageUrl && !imageError && <Typography>Carregando imagem da página…</Typography>}
      {imageError && <Alert severity="error">{imageError}</Alert>}
      {imageUrl && <Box sx={{ position: 'relative', width: '100%', border: 1, borderColor: 'divider' }}>
        <Image unoptimized src={imageUrl} alt={`Página ${pagina.numero} de ${anexo.nome}`} width={pagina.largura_imagem || 1200} height={pagina.altura_imagem || 1700} style={{ width: '100%', height: 'auto', display: 'block' }} />
        {box && pagina.largura_imagem > 0 && pagina.altura_imagem > 0 && <Box aria-label="Localização do trecho reconhecido" sx={{ position: 'absolute', pointerEvents: 'none', border: '2px solid #b45309', bgcolor: '#fbbf2433', left: `${100*box.x/pagina.largura_imagem}%`, top: `${100*box.y/pagina.altura_imagem}%`, width: `${100*box.largura/pagina.largura_imagem}%`, height: `${100*box.altura/pagina.altura_imagem}%` }} />}
      </Box>}
    </>}
    {pagina.metodo !== 'ocr_local' && pagina.texto && <>
      <Typography fontWeight={600} sx={{ mt: 2 }}>{anexo.mime === 'text/plain' ? 'Texto recebido' : 'Texto extraído do PDF'}</Typography>
      <Typography component="pre" sx={textStyle}>{pagina.texto}</Typography>
      <Button disabled={['referencia_redacao', 'nao_utilizar'].includes(anexo.organizacao?.finalidade || 'pendente')} onClick={() => selectSource(pagina.texto, 'texto')}>Usar trecho na ficha</Button>
    </>}
    {pagina.texto_ocr && <>
      <Typography fontWeight={600} sx={{ mt: 2 }}>Proposta do OCR local · {pagina.ocr_idioma || 'idioma não informado'}</Typography>
      <Typography variant="body2">Confira na imagem. O OCR não comprova que nomes ou números estejam corretos.</Typography>
      <Typography component="pre" sx={textStyle}>{pagina.texto_ocr}</Typography>
      <Button disabled={['referencia_redacao', 'nao_utilizar'].includes(anexo.organizacao?.finalidade || 'pendente')} onClick={() => selectSource(pagina.texto_ocr, 'ocr')}>Revisar trecho do OCR</Button>
      {pagina.regioes_ocr.length > 0 && <Stack spacing={1} sx={{ mt: 1 }}>
        <Typography variant="caption">Selecione uma linha para localizar na imagem. Não há pontuação de confiança disponível.</Typography>
        {pagina.regioes_ocr.map((line, index) => <Stack key={index} direction="row" gap={1} alignItems="start">
          <Button size="small" onClick={() => { setRegion(index); setShowImage(true) }} sx={{ textAlign: 'left', justifyContent: 'flex-start', overflowWrap: 'anywhere' }}>{line.texto}</Button>
          <Button size="small" disabled={['referencia_redacao', 'nao_utilizar'].includes(anexo.organizacao?.finalidade || 'pendente')} onClick={() => selectSource(line.texto, 'ocr')}>Usar linha</Button>
        </Stack>)}
      </Stack>}
    </>}
    {!pagina.texto && !pagina.texto_ocr && <Typography>Nenhum texto pôde ser reconhecido. Confira o original ou envie outra cópia.</Typography>}
  </Box>
}
