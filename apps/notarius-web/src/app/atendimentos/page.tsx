'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Box, Button, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material'
import { situacoesAtendimento } from '@/components/atendimentos/OrganizacaoAtendimento'
import { MainLayout } from '@/components/layout/main-layout'
import { atendimentosApi } from '@/lib/atendimentos'
import { useTenantStore } from '@/store/slices/tenantSlice'
import { useAuthStore } from '@/store/slices/authSlice'

export default function AtendimentosPage() {
  const router = useRouter()
  const cache = useQueryClient()
  const { selectedTenant } = useTenantStore()
  const { user } = useAuthStore()
  const [titulo, setTitulo] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [busca, setBusca] = useState('')
  const [situacao, setSituacao] = useState('')
  const [filters, setFilters] = useState({ busca: '', situacao: '' })
  const key = ['atendimentos', user?.id, selectedTenant?.id, filters]
  const query = useQuery({ queryKey: key, queryFn: () => atendimentosApi.list(filters), enabled: !!user && !!selectedTenant })

  async function create(event: React.FormEvent) {
    event.preventDefault()
    if (!titulo.trim() || saving) return
    setSaving(true)
    setError('')
    try {
      const item = await atendimentosApi.create(titulo.trim())
      await cache.invalidateQueries({ queryKey: ['atendimentos'] })
      router.push(`/atendimentos/${item.id}`)
    } catch {
      setError('Não foi possível confirmar a criação. Atualize a lista antes de tentar novamente.')
    } finally { setSaving(false) }
  }

  return <MainLayout>
    <Stack spacing={3} sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Box><Typography variant="h4" component="h1" fontWeight={700}>Atendimentos</Typography>
        <Typography color="text.secondary">Compra e venda · abra um atendimento e registre as informações da conversa.</Typography></Box>
      <Alert severity="warning">Piloto local acompanhado: confira o cartório e o atendimento. O padrão e o cenário exigem aprovação explícita da escrevente. A IA documental está indisponível; os dados podem ser registrados manualmente com suas fontes. Exemplos e aprovações simuladas não homologam um caso real.</Alert>
      <Paper component="form" onSubmit={create} sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h6" component="h2">Novo atendimento de compra e venda</Typography>
          <TextField label="Título do atendimento" placeholder="Ex.: Compra e venda · caso de teste" value={titulo}
            onChange={e => setTitulo(e.target.value)} slotProps={{ htmlInput: { maxLength: 160 } }} required disabled={saving} />
          {error && <Alert severity="error">{error}</Alert>}
          <Button type="submit" variant="contained" disabled={saving || !titulo.trim() || !selectedTenant} sx={{ alignSelf: 'flex-start' }}>
            {saving ? 'Criando…' : 'Criar atendimento'}</Button>
        </Stack>
      </Paper>
      <Typography variant="h6" component="h2">Atendimentos salvos</Typography>
      <Paper component="form" onSubmit={event => { event.preventDefault(); setFilters({ busca: busca.trim(), situacao }) }} sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} gap={2}>
          <TextField label="Buscar pelo título" value={busca} onChange={e => setBusca(e.target.value)} slotProps={{ htmlInput: { maxLength: 160 } }} sx={{ flex: 1 }} />
          <TextField select label="Situação" value={situacao} onChange={e => setSituacao(e.target.value)} sx={{ minWidth: 200 }}>
            <MenuItem value="">Todas</MenuItem>{Object.entries(situacoesAtendimento).map(([value,label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <Button type="submit">Buscar</Button>
          <Button onClick={() => { setBusca(''); setSituacao(''); setFilters({ busca: '', situacao: '' }) }}>Limpar filtros</Button>
        </Stack>
      </Paper>
      {!selectedTenant && <Alert severity="warning">Selecione um cartório para continuar.</Alert>}
      {query.isLoading && <CircularProgress aria-label="Carregando atendimentos" />}
      {query.isError && <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não foi possível carregar os atendimentos.</Alert>}
      {query.isSuccess && query.data.length === 0 && <Paper sx={{ p: 3 }}><Typography>Nenhum atendimento encontrado com os filtros atuais.</Typography></Paper>}
      {query.isSuccess && query.data.map(item => <Paper key={item.id} sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ sm: 'center' }}>
          <Box><Typography variant="h6" sx={{ overflowWrap: 'anywhere' }}>{item.titulo}</Typography>
            <Typography variant="body2">{situacoesAtendimento[item.situacao]}</Typography>
            <Typography variant="body2" color="text.secondary">Compra e venda · atualizado em {new Date(item.updated_at).toLocaleString('pt-BR')}</Typography></Box>
          <Button component={Link} href={`/atendimentos/${item.id}`} variant="outlined">Abrir atendimento</Button>
        </Stack>
      </Paper>)}
    </Stack>
  </MainLayout>
}
