'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type MinutaPreparada } from '@/lib/atendimentos'

export function ComparacaoMinuta({ id, scope, atual, versoes, disabled }: { id: string; scope: (string | undefined)[]; atual: MinutaPreparada; versoes: MinutaPreparada[]; disabled: boolean }) {
  const alternatives = versoes.filter(v => v.id !== atual.id)
  const [open, setOpen] = useState(false)
  const [base, setBase] = useState(alternatives.find(v => v.versao < atual.versao)?.id || alternatives[0]?.id || '')
  const [unchanged, setUnchanged] = useState(false)
  const query = useQuery({ queryKey: ['comparacao-minutas', ...scope, base, atual.id], queryFn: () => atendimentosApi.compararMinutas(id, base, atual.id), enabled: open && !!base, retry: false })
  return <>
    <Button disabled={disabled || !alternatives.length} onClick={() => setOpen(true)}>Comparar versões</Button>
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md">
      <DialogTitle>Comparar com a minuta v{atual.versao}</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <TextField select label="Versão de referência (antes)" value={base} onChange={e => setBase(e.target.value)}>
          {alternatives.map(v => <MenuItem key={v.id} value={v.id}>v{v.versao}{v.tipo === 'editada' ? ' · editada' : ''}{v.desatualizada ? ' · desatualizada' : ''}</MenuItem>)}
        </TextField>
        <Typography>A referência é o texto anterior na comparação; a versão de destino é v{atual.versao}. Consultar o histórico não libera edição ou exportação de versões desatualizadas.</Typography>
        {query.isFetching && <Typography role="status">Comparando textos salvos…</Typography>}
        {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não consegui carregar a comparação. Nenhum resultado anterior deve ser usado.</Alert>}
        {query.isSuccess && !query.isFetching && <>
          <Alert severity="info">{query.data.aviso}</Alert>
          <Typography>Modelo da referência: v{query.data.base.modelo_versao} · Modelo do destino: v{query.data.destino.modelo_versao}</Typography>
          {query.data.comparacao_simplificada && <Alert severity="warning">Texto com muitas linhas. Exibo os blocos completos para manter a comparação disponível.</Alert>}
          {!query.data.texto_alterado && <Alert severity="info">O texto é idêntico nas duas versões.</Alert>}
          <FormControlLabel control={<Checkbox checked={unchanged} onChange={e => setUnchanged(e.target.checked)} />} label="Mostrar também trechos sem alteração" />
          {query.data.trechos.filter(p => unchanged || p.tipo !== 'igual').map((part, i) => <Box key={i} sx={{ p: 2, borderLeft: 4, borderColor: part.tipo === 'removido' ? 'error.main' : part.tipo === 'adicionado' ? 'success.main' : 'divider', bgcolor: 'action.hover' }}>
            <Typography fontWeight={600}>{part.tipo === 'removido' ? `Removido da referência v${query.data.base.versao}` : part.tipo === 'adicionado' ? `Acrescentado no destino v${query.data.destino.versao}` : 'Sem alteração'}</Typography>
            <Typography component="pre" sx={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{part.texto}</Typography>
          </Box>)}
          <Typography variant="h6">Dados usados na preparação</Typography>
          {!query.data.dados_alterados.length && <Typography>As duas versões usam os mesmos registros da ficha. Edições manuais do texto podem existir sem alterar esses registros.</Typography>}
          {query.data.dados_alterados.map(field => <Box key={field.chave} sx={{ p: 2, bgcolor: 'action.hover' }}>
            <Typography fontWeight={600}>{field.rotulo}</Typography>
            {!field.valor_alterado && <Typography variant="body2">O valor permaneceu igual; mudou a revisão, situação ou origem registrada.</Typography>}
            <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>Antes: {field.antes?.valor ?? 'Sem registro'}</Typography>
            <Typography variant="caption">Revisão {field.antes?.versao ?? '—'} · {field.antes?.situacao ?? '—'}</Typography>
            <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>Depois: {field.depois?.valor ?? 'Sem registro'}</Typography>
            <Typography variant="caption">Revisão {field.depois?.versao ?? '—'} · {field.depois?.situacao ?? '—'}</Typography>
          </Box>)}
        </>}
      </Stack></DialogContent>
      <DialogActions><Button onClick={() => setOpen(false)}>Voltar à minuta</Button></DialogActions>
    </Dialog>
  </>
}
