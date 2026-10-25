'use client'

import { Alert, Box, Button, Stack, Typography } from '@mui/material'
import type { PadraoPiloto } from '@/lib/atendimentos'

export function RevisaoPadraoPiloto({ padrao, disabled, onLoad }: { padrao: PadraoPiloto; disabled: boolean; onLoad: () => void }) {
  return <Box>
    <Typography fontWeight={600}>Padrão para o piloto acompanhado</Typography>
    <Typography variant="body2">Uma pessoa vendedora, uma compradora, um imóvel, participação direta e pagamento previsto. Hipótese para decisão da escrevente.</Typography>
    <Button disabled={disabled} onClick={onLoad}>Carregar padrão do piloto como rascunho</Button>
    <Typography variant="caption" display="block">Substitui apenas o texto em edição. As versões já salvas são preservadas; nenhuma aprovação é recuperada.</Typography>
    <Box component="details" sx={{ mt: 1 }}>
      <Typography component="summary" sx={{ cursor: 'pointer' }}>Revisão simples da escrevente · {padrao.versao}</Typography>
      <Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="info">{padrao.aviso} Este roteiro descreve o candidato oferecido; confira também todas as alterações feitas no texto e nas posições abaixo antes de aprovar.</Alert>
        <Typography fontWeight={600}>Decisões necessárias</Typography>
        {padrao.decisoes.map((decision, index) => <Typography key={decision} variant="body2">{index + 1}. {decision}</Typography>)}
        <Typography fontWeight={600}>Texto candidato · espaços entre ⟦ ⟧ exigem dados do caso</Typography>
        <Box sx={{ maxHeight: 400, overflow: 'auto', p: 1, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{padrao.texto_candidato}</Typography>
        </Box>
        <Typography fontWeight={600}>Aplicação e confirmações por seção</Typography>
        {padrao.revisao.map(section => <Box key={section.chave}>
          <Typography variant="body2" fontWeight={600}>{section.rotulo}</Typography>
          <Typography variant="body2">{section.condicao}</Typography>
          <Typography variant="caption">Origem da estrutura: {section.origem}. Não é fonte dos fatos do atendimento.</Typography>
        </Box>)}
        <Typography fontWeight={600}>Limites do preenchimento</Typography>
        {padrao.limites.map(limit => <Typography key={limit} variant="body2">{limit}</Typography>)}
      </Stack>
    </Box>
  </Box>
}
