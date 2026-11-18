import { useState } from 'react'
import { Alert, Box, Button, Stack, Typography } from '@mui/material'
import type { ComparacaoAnexos, EvidenciaAnexo } from '@/lib/atendimentos'

const estado = {
  divergencia: 'Divergência',
  possivel_divergencia: 'Possível divergência',
  conferir_leitura: 'Conferir no original',
  conferir_vinculo: 'Confirmar destinatário',
  sugestao: 'Sugestão para a ficha',
  coincidencia: 'Valores coincidentes',
}
const problemas = {
  ausente: 'Sem valor informado',
  formato_invalido: 'Valor ou formato precisa de conferência',
  leitura_incerta: 'Leitura incerta',
}

export function ConferenciaAnexosChat({ report, onSource }: {
  report: ComparacaoAnexos; onSource: (source: EvidenciaAnexo) => void
}) {
  const [showAll, setShowAll] = useState(false)
  const conflicts = report.grupos.filter(group => ['divergencia', 'possivel_divergencia'].includes(group.estado)).length
  const groups = showAll ? report.grupos : report.grupos.slice(0, 5)
  return <Stack component="section" aria-label="Comparação dos anexos" spacing={1.25} sx={{ mt: 2 }}>
    <Typography component="h2" variant="subtitle2">Comparação dos anexos</Typography>
    {report.limitado && <Alert severity="warning">A comparação atingiu o limite de leitura. Confira também os demais trechos nos originais.</Alert>}
    {report.total_sugestoes ? <>
      <Typography variant="body2">
        {report.total_sugestoes} trecho(s) com campos reconhecidos{conflicts ? ` · ${conflicts} campo(s) com valores diferentes para conferir` : ''}.
        Confira os originais e registre sua decisão na ficha.
      </Typography>
      {groups.map(group => <Box key={group.id} component="details" sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 1.5 }}>
        <Box component="summary" sx={{ cursor: 'pointer', overflowWrap: 'anywhere' }}>
          <Typography component="span" variant="body2" fontWeight={650}>{group.rotulo}</Typography>
          <Typography component="span" variant="caption" color="text.secondary"> · {estado[group.estado]}{group.objeto_id ? ` · registro ${group.objeto_id.slice(0, 8)}` : ''}</Typography>
        </Box>
        <Typography variant="body2" sx={{ my: 1 }}>{group.pergunta}</Typography>
        <Stack spacing={1}>
          {group.fontes.map(source => <Box key={`${source.pagina_id}:${source.canal}:${source.linha}`} sx={{ bgcolor: 'background.paper', p: 1.25, borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
              {source.arquivo} · página {source.pagina} · {source.canal === 'ocr' ? 'OCR' : 'texto'} · linha {source.linha} · leitura v{source.leitura_versao}
            </Typography>
            <Typography component="blockquote" variant="body2" sx={{ m: 0, mt: .5, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{source.trecho}</Typography>
            {!!source.problemas.length && <Typography variant="caption" display="block" color="text.secondary">{source.problemas.map(problem => problemas[problem]).join(' · ')}</Typography>}
            <Button size="small" onClick={() => onSource(source)} aria-label={`Conferir fonte de ${group.rotulo} em ${source.arquivo}, página ${source.pagina}`}>Conferir fonte</Button>
          </Box>)}
        </Stack>
      </Box>)}
      {report.grupos.length > 5 && <Button size="small" onClick={() => setShowAll(value => !value)} sx={{ alignSelf: 'flex-start' }}>
        {showAll ? 'Mostrar menos campos' : `Mostrar todos os ${report.grupos.length} campos`}
      </Button>}
    </> : <Typography variant="body2" color="text.secondary">Nenhum campo com rótulo reconhecido na leitura atual. Confira os documentos e registre os dados na ficha.</Typography>}
  </Stack>
}
