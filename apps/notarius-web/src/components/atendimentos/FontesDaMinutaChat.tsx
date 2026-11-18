import { Box, Button, Stack, Typography } from '@mui/material'
import type { MinutaPreparada, PedidoDocumento } from '@/lib/atendimentos'
import { origemDaMinuta } from '@/lib/chatAtendimento'

const rotulos: Record<string, string> = {
  descricao: 'Descrição', imovel: 'Imóvel', preco: 'Preço informado',
  pagamento: 'Forma de pagamento', situacao_pagamento: 'Situação do pagamento',
  quitacao: 'Declaração de quitação',
}
const destaques = ['imovel', 'situacao_pagamento', 'quitacao']
const camposObrigatoriosLegados = ['vendedores', 'compradores', 'imovel', 'preco', 'pagamento']

export function FontesDaMinutaChat({ minuta, onSource }: {
  minuta: MinutaPreparada
  onSource: (source: Omit<PedidoDocumento, 'token' | 'acao'>) => void
}) {
  const inseridos = minuta.campos_inseridos ?? Object.keys(minuta.dados).filter(key =>
    minuta.dados[key].ocorrencias?.length || camposObrigatoriosLegados.includes(key))
  const fields = inseridos.flatMap(key => {
    const data = minuta.dados[key]
    if (!data || (data.situacao !== 'confirmado' && data.situacao !== 'sugerido')) return []
    const field = key.split('.').at(-1) || key
    const propertyDescription = data.tipo === 'imovel' && field === 'descricao'
    const label = propertyDescription ? 'Descrição do imóvel' : rotulos[field] || field.replaceAll('_', ' ')
    const origem = origemDaMinuta(data.origem)
    const { anexo_id, pagina_id, leitura_versao } = origem?.tipo === 'documento' ? origem : {}
    const source = anexo_id && pagina_id ? { anexo_id, pagina_id, leitura_versao } : null
    return [{ key, field: propertyDescription ? 'imovel' : field, label, origem, source, valor: data.valor }]
  })
  if (!fields.length) return null

  const files = new Set(fields.flatMap(({ origem }) => origem?.tipo === 'documento' && origem.arquivo ? [origem.anexo_id || origem.arquivo] : []))
  const highlights = destaques.flatMap(field => fields.filter(row => row.field === field)).slice(0, 3)
  const edited = minuta.tipo === 'editada' || minuta.ocorrencias_correspondem_texto === false

  return <Stack spacing={.75} sx={{ mt: 1.5, overflowWrap: 'anywhere' }}>
    <Typography variant="subtitle2">{edited ? 'Fontes da versão de base' : `Fontes da minuta v${minuta.versao}`}</Typography>
    {edited && <Typography variant="body2" color="text.secondary">Confira as edições manuais no editor. As fontes abaixo são do preenchimento original.</Typography>}
    {highlights.map(({ key, field, label, origem, valor }) => <Typography key={key} variant="body2">
      <strong>{label}</strong>{field === 'situacao_pagamento' ? ` · ${valor.replaceAll('_', ' ')}` : field === 'quitacao' ? ` · ${valor}` : ''}
      {origem?.tipo === 'documento' && origem.arquivo ? ` · ${origem.arquivo}` : ''}
    </Typography>)}
    <Box component="details">
      <Box component="summary" sx={{ cursor: 'pointer', fontSize: 14 }}>
        {fields.length} {fields.length === 1 ? 'campo preenchido' : 'campos preenchidos'}{files.size > 0 && ` · ${files.size} ${files.size === 1 ? 'arquivo como fonte' : 'arquivos como fonte'}`}
      </Box>
      <Stack spacing={1.25} sx={{ mt: 1 }}>
        {fields.map(({ key, label, origem, source }) => <Box key={key}>
          <Typography variant="body2" fontWeight={600} sx={{ textTransform: 'capitalize' }}>{label}{key.includes('.') ? ` · ${key.split('.')[0]}` : ''}</Typography>
          <Typography variant="caption" display="block">
            {origem?.tipo === 'documento' ? [origem.arquivo, origem.pagina && `página ${origem.pagina}`, origem.canal === 'ocr' && 'OCR', origem.leitura_versao && `leitura v${origem.leitura_versao}`].filter(Boolean).join(' · ')
              : origem?.tipo === 'mensagem' ? 'Mensagem do atendimento' : origem?.tipo === 'manual' ? 'Registro manual' : 'Origem não registrada'}
          </Typography>
          {origem?.trecho && <Typography component="blockquote" variant="body2" sx={{ m: 0, whiteSpace: 'pre-wrap' }}>{origem.trecho}</Typography>}
          {source && <Button size="small" onClick={() => onSource(source)}>Conferir fonte de {label}</Button>}
          {origem?.origem_papel?.anexo_id && origem.origem_papel.pagina_id && <Button size="small" onClick={() => {
            const papel = origem.origem_papel
            if (papel?.anexo_id && papel.pagina_id) onSource({ anexo_id: papel.anexo_id, pagina_id: papel.pagina_id, leitura_versao: papel.leitura_versao })
          }}>Conferir papel na negociação</Button>}
        </Box>)}
      </Stack>
    </Box>
  </Stack>
}
