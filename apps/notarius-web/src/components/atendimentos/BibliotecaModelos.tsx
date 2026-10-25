'use client'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TextField, Typography } from '@mui/material'
import { atendimentosApi, type ModeloBiblioteca, type ModeloMinuta } from '@/lib/atendimentos'

export function BibliotecaModelos({ id, scope, current, canPublish, onLoad }: { id: string; scope: (string | undefined)[]; current?: ModeloMinuta; canPublish: boolean; onLoad: (model: ModeloBiblioteca) => void }) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const [publish, setPublish] = useState(false)
  const [search, setSearch] = useState('')
  const [term, setTerm] = useState('')
  const [selected, setSelected] = useState<ModeloBiblioteca | null>(null)
  const [name, setName] = useState('')
  const [checked, setChecked] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const query = useQuery({ queryKey: ['biblioteca-modelos', ...scope, term], queryFn: () => atendimentosApi.bibliotecaModelos(term), enabled: open, retry: false })
  async function save() {
    if (!current || !checked || busy) return
    setBusy(true); setError('')
    try {
      await atendimentosApi.publicarModelo(id, current.id, name.trim())
      await cache.invalidateQueries({ queryKey: ['biblioteca-modelos'] })
      setPublish(false); setSuccess('Modelo publicado na biblioteca deste cartório. A reutilização exigirá revisão no novo atendimento.')
    } catch { setError('Não consegui publicar. Confira se esta ainda é a versão atual e aprovada do modelo e tente novamente.') }
    finally { setBusy(false) }
  }
  const block = (title: string, text: string) => text && <Box><Typography fontWeight={600}>{title}</Typography><Typography component="pre" sx={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', bgcolor: 'action.hover', p: 2 }}>{text}</Typography></Box>
  return <>
    <Stack direction="row" gap={1} flexWrap="wrap">
      <Button onClick={() => { setOpen(true); setSelected(null) }}>Carregar da biblioteca</Button>
      <Button disabled={!canPublish || !current?.aprovado} onClick={() => { setPublish(true); setChecked(false); setName(''); setError(''); setSuccess('') }}>Publicar modelo salvo na biblioteca</Button>
    </Stack>
    {success && <Alert severity="success">{success}</Alert>}
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md"><DialogTitle>Modelos do cartório</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="info">Carregar copia apenas o padrão publicado para o editor. Não copia dados da ficha nem a aprovação de outro atendimento. Confira se o padrão é aplicável ao novo caso.</Alert>
        <Stack direction="row" gap={1}><TextField label="Buscar modelo pelo nome" value={search} onChange={e => setSearch(e.target.value)} slotProps={{ htmlInput: { maxLength: 120 } }} /><Button onClick={() => { setTerm(search.trim()); setSelected(null) }}>Buscar</Button></Stack>
        {query.isFetching && <Typography>Carregando biblioteca…</Typography>}
        {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não consegui consultar a biblioteca.</Alert>}
        {query.isSuccess && !query.isFetching && <>
          {!query.data.modelos.length && <Typography>Nenhum modelo publicado com esse nome. Para publicar, revise e salve um modelo aprovado sem dados específicos de um atendimento.</Typography>}
          {query.data.mais_resultados && <Typography>Exibindo 50 modelos. Refine a busca pelo nome.</Typography>}
          {query.data.modelos.map(model => <Button key={model.id} onClick={() => setSelected(model)} sx={{ justifyContent: 'flex-start', textAlign: 'left' }}>{model.nome} · {model.autor_nome} · {new Date(model.created_at).toLocaleDateString('pt-BR')}</Button>)}
        </>}
        {selected && <>
          <Typography variant="h6">{selected.nome}</Typography>
          {block('Corpo principal',selected.corpo)}{block('Representação',selected.representacao)}{block('Observações',selected.observacoes)}
          <Alert severity="warning">Carregar substitui os textos atualmente no editor. Nada será salvo até você revisar e salvar o modelo neste atendimento.</Alert>
          <Button variant="contained" onClick={() => { onLoad(selected); setOpen(false) }}>Carregar no editor para revisão</Button>
        </>}
      </Stack></DialogContent><DialogActions><Button onClick={() => setOpen(false)}>Voltar ao modelo</Button></DialogActions>
    </Dialog>
    <Dialog open={publish} onClose={() => !busy && setPublish(false)} fullWidth maxWidth="md"><DialogTitle>Publicar modelo salvo v{current?.versao}</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <Alert severity="warning">Este padrão ficará disponível aos usuários do mesmo cartório. Retire nomes, identificadores, endereços, valores e declarações específicas do caso. O sistema não anonimiza o texto automaticamente. Se encontrar esses dados abaixo, volte e corrija o modelo antes de publicar.</Alert>
        {block('Corpo principal salvo',current?.corpo || '')}{block('Representação salva',current?.representacao || '')}{block('Observações salvas',current?.observacoes || '')}
        <TextField label="Nome do padrão (sem dados pessoais)" value={name} onChange={e => setName(e.target.value)} disabled={busy} slotProps={{ htmlInput: { maxLength: 120 } }} />
        <FormControlLabel control={<Checkbox checked={checked} disabled={busy} onChange={e => setChecked(e.target.checked)} />} label="Conferi o texto e confirmo que contém apenas o padrão e marcadores, sem dados de pessoas ou negócios." />
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setPublish(false)}>Voltar sem publicar</Button><Button variant="contained" disabled={busy || !checked || !name.trim()} onClick={save}>{busy ? 'Publicando…' : 'Publicar no cartório'}</Button></DialogActions>
    </Dialog>
  </>
}
