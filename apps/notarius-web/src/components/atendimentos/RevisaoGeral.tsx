'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Typography } from '@mui/material'
import { atendimentosApi, type ResumoRevisao } from '@/lib/atendimentos'

const labels: Record<string,string> = { ausente:'Ausente', informado:'Informado, sem confirmação', confirmado:'Confirmado pela escrevente', divergente:'Divergente', ilegivel:'Leitura incerta' }
function source(data: ResumoRevisao['campos'][number]['atual']) {
  if (!data) return 'Sem origem registrada'
  const origin = data.origem
  return origin.tipo === 'documento' ? `${origin.arquivo} · página ${origin.pagina} · leitura v${origin.leitura_versao ?? '?'}${origin.canal === 'ocr' ? ' · OCR' : ''}` : origin.tipo === 'mensagem' ? 'Mensagem da conversa' : 'Registro manual'
}
function download(data: ResumoRevisao) {
  const lines = ['RESUMO PARA REVISÃO — NÃO É MINUTA OU APROVAÇÃO DO ATO', data.atendimento.titulo,
    `Consulta: ${new Date(data.gerado_em).toLocaleString('pt-BR')}`, data.aviso, '',
    data.pronto_para_preparar ? 'Verificações iniciais permitem preparar a minuta; revisão integral ainda necessária.' : `Preparação bloqueada: ${data.motivo_bloqueio}`, '', 'DADOS REGISTRADOS']
  data.campos.forEach(field => lines.push('', field.rotulo, `Situação: ${field.atual ? labels[field.atual.situacao] : 'Não registrado'}`,
    field.atual?.valor || '(sem valor)', `Origem: ${source(field.atual)}`, `Trecho: ${field.atual?.origem.trecho || '(sem trecho)'}`,
    `Revisão: ${field.atual?.versao ?? '—'} · ${field.atual?.autor_nome || '—'}`, `Motivo: ${field.atual?.justificativa || '—'}`))
  lines.push('', 'DOCUMENTOS')
  data.documentos.forEach(doc => lines.push('', `${doc.nome} · leitura v${doc.leitura_versao}`, doc.aviso,
    doc.revisao_manual ? `Revisão manual: ${doc.revisao_manual.autor_nome} · ${doc.revisao_manual.justificativa}` : 'Revisão manual da leitura atual pendente.'))
  lines.push('', 'PENDÊNCIAS', ...data.pendencias.map(p => `${p.rotulo}: ${p.pergunta}`), '',
    `Modelo: ${data.modelo ? `v${data.modelo.versao} · ${data.modelo.aprovado ? 'aprovado para o atendimento' : 'rascunho'}` : 'não registrado'}`,
    `Minuta: ${data.minuta ? `v${data.minuta.versao} · ${data.minuta.desatualizada ? 'desatualizada' : 'compatível com os registros da consulta'}` : 'não preparada'}`,
    `Revisão final: ${data.minuta?.revisao_final ? `${data.minuta.revisao_final.autor_nome} · ${data.minuta.revisao_final.created_at} · ${data.minuta.revisao_final.texto_corresponde ? 'texto correspondente' : 'texto não corresponde'}` : 'não registrada'}`,
    '', 'Este arquivo é uma fotografia dos registros na data da consulta. Alterações posteriores não atualizam esta cópia.')
  const url = URL.createObjectURL(new Blob(['\ufeff'+lines.join('\r\n')], { type:'text/plain;charset=utf-8' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `resumo-revisao-${data.atendimento.id}.txt`; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
export function RevisaoGeral({ id, scope }: { id: string; scope: (string | undefined)[] }) {
  const [open, setOpen] = useState(false)
  const query = useQuery({ queryKey: ['resumo-revisao', ...scope], queryFn: () => atendimentosApi.resumoRevisao(id), enabled: open, retry: false, refetchOnWindowFocus: true })
  const data = query.isSuccess && !query.isFetching ? query.data : null
  return <>
    <Button variant="outlined" onClick={() => setOpen(true)}>Ver resumo de conferência</Button>
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md"><DialogTitle>Revisão geral do atendimento</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        {query.isFetching && <Typography role="status">Conferindo os registros atuais…</Typography>}
        {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Atualizar</Button>}>Não consegui obter um resumo atual. Não use uma consulta anterior para continuar.</Alert>}
        {data && <>
          <Typography fontWeight={600} sx={{ overflowWrap: 'anywhere' }}>{data.atendimento.titulo}</Typography>
          <Typography variant="caption">Consulta de {new Date(data.gerado_em).toLocaleString('pt-BR')}. Atualize após mudanças.</Typography>
          <Alert severity="info">{data.aviso}</Alert>
          <Alert severity={data.pronto_para_preparar ? 'info' : 'warning'}>{data.pronto_para_preparar ? 'Verificações iniciais permitem preparar a minuta. Isso não substitui sua revisão integral.' : `Preparação bloqueada: ${data.motivo_bloqueio}`}</Alert>
          <Typography variant="h6">Pendências ({data.pendencias.length})</Typography>
          {data.pendencias.map(p => <Box key={p.chave} sx={{ p: 2, bgcolor: 'action.hover' }}><Typography fontWeight={600}>{p.rotulo}</Typography><Typography>{p.pergunta}</Typography></Box>)}
          {!data.pendencias.length && <Typography>Nenhuma pendência nas verificações iniciais do sistema.</Typography>}
          <Typography variant="h6">Dados e fontes</Typography>
          {data.campos.map(field => <Box key={field.chave} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Typography fontWeight={600}>{field.rotulo}{field.obrigatorio ? '' : ' · opcional no protótipo'}</Typography>
            <Typography variant="body2">{field.atual ? labels[field.atual.situacao] : 'Não registrado'}</Typography>
            {data.pendencias.some(p => p.chave === field.chave) && <Typography color="warning.main" variant="body2">Este campo tem uma pendência atual. A confirmação de um registro anterior não resolve automaticamente novas divergências.</Typography>}
            <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', my: 1 }}>{field.atual?.valor || 'Sem valor registrado'}</Typography>
            <Typography variant="body2">Origem: {source(field.atual)}</Typography>
            {field.atual?.origem.trecho && <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: 180, overflow: 'auto', bgcolor: 'action.hover', p: 1 }}>{field.atual.origem.trecho}</Typography>}
            {field.atual && <><Typography variant="caption">Revisão {field.atual.versao} · {field.atual.autor_nome} · {new Date(field.atual.created_at).toLocaleString('pt-BR')}</Typography><Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>Motivo: {field.atual.justificativa}</Typography></>}
          </Box>)}
          <Typography variant="h6">Documentos ({data.documentos.length})</Typography>
          {!data.documentos.length && <Typography>Nenhum documento anexado.</Typography>}
          {data.documentos.map(doc => <Box key={doc.id} sx={{ p: 2, bgcolor: 'action.hover' }}>
            <Typography fontWeight={600} sx={{ overflowWrap: 'anywhere' }}>{doc.nome} · leitura v{doc.leitura_versao}</Typography>
            <Typography>{doc.paginas} página(s) na leitura · {doc.paginas_ocr} com texto OCR</Typography>
            <Typography>{doc.aviso}</Typography>
            <Typography fontWeight={600}>{doc.revisao_manual ? `Revisão manual registrada por ${doc.revisao_manual.autor_nome}` : 'Revisão manual da leitura atual pendente'}</Typography>
            {doc.revisao_manual && <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{doc.revisao_manual.justificativa}</Typography>}
          </Box>)}
          <Typography variant="h6">Modelo e minuta</Typography>
          <Typography>Modelo: {data.modelo ? `v${data.modelo.versao} · ${data.modelo.aprovado ? 'aprovado para este atendimento' : 'rascunho'}` : 'não registrado'}</Typography>
          <Typography>Minuta: {data.minuta ? `v${data.minuta.versao} · ${data.minuta.desatualizada ? 'desatualizada' : 'compatível com os registros desta consulta'}` : 'não preparada'}</Typography>
          {data.minuta && <Typography>Revisão final: {data.minuta.revisao_final ? `registrada por ${data.minuta.revisao_final.autor_nome}${data.minuta.revisao_final.texto_corresponde ? '' : ' · texto não corresponde; exportação bloqueada'}` : 'pendente antes da exportação'}</Typography>}
          <Typography variant="caption">O resumo baixado contém os dados exibidos e não acompanha alterações futuras. Guarde-o conforme os cuidados aplicáveis aos documentos do atendimento.</Typography>
        </>}
      </Stack></DialogContent><DialogActions><Button onClick={() => setOpen(false)}>Voltar à conversa</Button><Button disabled={query.isFetching} onClick={() => query.refetch()}>Atualizar resumo</Button><Button disabled={!data} onClick={() => data && download(data)}>Baixar resumo TXT</Button></DialogActions>
    </Dialog>
  </>
}
