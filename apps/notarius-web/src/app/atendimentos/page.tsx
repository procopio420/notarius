'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box, Button, Chip, CircularProgress, IconButton, InputAdornment, Paper, Stack, TextField, Typography } from '@mui/material'
import { ArrowRight, ArrowUpRight, Check, ChevronRight, FileText, FolderOpen, Plus, Search, X } from 'lucide-react'
import { NovoAtendimento } from '@/components/atendimentos/NovoAtendimento'
import { AtendimentoLayout } from '@/components/atendimentos/AtendimentoLayout'
import { situacoesAtendimento } from '@/components/atendimentos/OrganizacaoAtendimento'
import { atendimentosApi, type Atendimento } from '@/lib/atendimentos'
import { useTenantStore } from '@/store/slices/tenantSlice'
import { useAuthStore } from '@/store/slices/authSlice'

const filtersList = [{ value: '', label: 'Todos' }, { value: 'em_andamento', label: 'Em andamento' }, { value: 'aguardando', label: 'Aguardando' }, { value: 'pausado', label: 'Pausados' }]
const statusStyles = {
  em_andamento: { color: '#325b45', bgcolor: '#edf4e8' },
  aguardando: { color: '#886024', bgcolor: '#fbf2df' },
  pausado: { color: '#68716d', bgcolor: '#eff1ee' },
}

function CaseRow({ item }: { item: Atendimento }) {
  return <Box component={Link} href={`/atendimentos/${item.id}`} sx={{ display: 'grid', gridTemplateColumns: { xs: '42px minmax(0, 1fr) 22px', md: '44px minmax(0, 1fr) 150px 115px 24px' }, alignItems: 'center', gap: { xs: 1.5, sm: 2 }, px: { xs: 2, sm: 3 }, py: 2.5, color: 'inherit', textDecoration: 'none', borderBottom: '1px solid #edf0ea', transition: 'background .18s', '&:last-child': { borderBottom: 0 }, '&:hover': { bgcolor: '#f7faf3' }, '&:focus-visible': { outline: '3px solid #91ad79', outlineOffset: -3 } }}>
    <Box sx={{ width: 42, height: 48, display: 'grid', placeItems: 'center', color: '#587361', bgcolor: '#f1f4ed', borderRadius: '10px' }}><FileText size={20} strokeWidth={1.6} /></Box>
    <Box sx={{ minWidth: 0 }}>
      <Typography sx={{ fontSize: 15, fontWeight: 650, overflowWrap: 'anywhere', lineHeight: 1.45 }}>{item.titulo}</Typography>
      <Stack direction="row" gap={1} alignItems="center" sx={{ mt: .5 }}>
        <Typography sx={{ color: 'text.secondary', fontSize: 12 }}>Compra e venda</Typography>
        <Box sx={{ display: { xs: 'block', md: 'none' }, color: statusStyles[item.situacao].color, fontSize: 11 }}>· {situacoesAtendimento[item.situacao]}</Box>
      </Stack>
    </Box>
    <Chip size="small" label={situacoesAtendimento[item.situacao]} sx={{ display: { xs: 'none', md: 'inline-flex' }, justifySelf: 'start', ...statusStyles[item.situacao], fontSize: 11, fontWeight: 650 }} />
    <Typography sx={{ display: { xs: 'none', md: 'block' }, fontSize: 12, color: 'text.secondary' }} title={new Date(item.updated_at).toLocaleString('pt-BR')}>{new Date(item.updated_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</Typography>
    <ChevronRight size={18} color="#7e8b80" />
  </Box>
}

export default function AtendimentosPage() {
  const { selectedTenant } = useTenantStore()
  const { user } = useAuthStore()
  const [creating, setCreating] = useState(false)
  const [busca, setBusca] = useState('')
  const [situacao, setSituacao] = useState('')
  const [term, setTerm] = useState('')
  useEffect(() => { const timer = setTimeout(() => setTerm(busca.trim()), 300); return () => clearTimeout(timer) }, [busca])
  const enabled = !!user && (process.env.NEXT_PUBLIC_PILOTO_LOCAL === '1' || !!selectedTenant)
  const query = useQuery({ queryKey: ['atendimentos', user?.id, selectedTenant?.id, { busca: term, situacao }], queryFn: () => atendimentosApi.list({ busca: term, situacao }), enabled })
  const hasFilters = !!term || !!situacao
  const latest = !hasFilters ? query.data?.[0] : undefined

  return <AtendimentoLayout>
    <Stack spacing={{ xs: 3, md: 4 }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} gap={2}>
        <Box>
          <Typography sx={{ fontSize: 11, letterSpacing: '1.8px', fontWeight: 700, color: '#708167', mb: 1 }}>SEU ESPAÇO DE TRABALHO</Typography>
          <Typography component="h1" sx={{ fontFamily: 'Georgia, serif', fontSize: { xs: 36, md: 44 }, letterSpacing: '-1.6px', color: '#203c35', lineHeight: 1.15 }}>Atendimentos</Typography>
          <Typography sx={{ color: 'text.secondary', mt: 1, fontSize: 14 }}>Tudo o que você precisa, do primeiro documento à minuta.</Typography>
        </Box>
        <Button variant="contained" startIcon={<Plus size={18} />} onClick={() => setCreating(true)} disabled={!enabled} sx={{ flexShrink: 0, whiteSpace: 'nowrap' }}>Novo atendimento</Button>
      </Stack>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1.65fr) minmax(0, 1fr)' }, gap: 2.5 }}>
        <Box sx={{ position: 'relative', overflow: 'hidden', borderRadius: '20px', bgcolor: '#254c40', color: '#fff', p: { xs: 3, sm: 4 }, minHeight: { xs: 180, md: 210 }, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', justifyContent: 'center' }}>
          <Box aria-hidden="true" sx={{ position: 'absolute', width: 200, height: 200, border: '1px solid #ffffff13', borderRadius: '50%', right: -60, top: -80 }} />
          <Stack direction="row" alignItems="center" gap={1} sx={{ color: '#d9edaa', mb: 1.5 }}><FolderOpen size={16} /><Typography sx={{ fontSize: 10, fontWeight: 700, letterSpacing: '1.5px' }}>{latest ? 'CONTINUE DE ONDE PAROU' : 'COMPRA E VENDA'}</Typography></Stack>
          <Typography component="h2" sx={{ fontFamily: 'Georgia, serif', fontSize: { xs: 24, sm: 28 }, lineHeight: 1.25, maxWidth: '95%', overflowWrap: 'anywhere', mb: 2 }}>{latest ? latest.titulo : 'Um atendimento bem organizado começa aqui.'}</Typography>
          {latest ? <Button component={Link} href={`/atendimentos/${latest.id}`} endIcon={<ArrowUpRight size={16} />} sx={{ color: '#e4f1cb', p: 0, minHeight: 32, '&:hover': { bgcolor: '#ffffff0a' } }}>Retomar atendimento</Button> : <Typography sx={{ fontSize: 13, color: '#d2e0d7', maxWidth: 360 }}>Reúna os documentos, confira os dados e prepare o texto no seu ritmo.</Typography>}
        </Box>
        <Paper elevation={0} sx={{ display: { xs: 'none', md: 'block' }, bgcolor: '#eef1e7', border: '1px solid #e3e8da', borderRadius: '20px', p: { xs: 3, sm: 3.5 } }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}><Typography sx={{ fontSize: 13, fontWeight: 700 }}>Um caminho simples</Typography><Box sx={{ color: '#718663' }}><ArrowUpRight size={18} /></Box></Stack>
          {['Escolha o serviço e os documentos', 'Converse e esclareça as dúvidas', 'Confira a minuta preparada'].map((label, index) => <Stack key={label} direction="row" alignItems="center" gap={1.5} sx={{ py: .75 }}><Box sx={{ display: 'grid', placeItems: 'center', width: 23, height: 23, border: '1px solid #cbd6be', borderRadius: '50%', fontSize: 11, color: '#54694a' }}>{index + 1}</Box><Typography sx={{ fontSize: 13, color: '#4d5d50' }}>{label}</Typography></Stack>)}
        </Paper>
      </Box>

      <Box>
        <Stack direction="row" justifyContent="space-between" alignItems="center" gap={2} sx={{ mb: 2 }}>
          <Stack direction="row" alignItems="center" gap={1}><Typography component="h2" sx={{ fontSize: 18, fontWeight: 650 }}>Seus atendimentos</Typography>{query.isSuccess && <Box sx={{ fontSize: 11, bgcolor: '#e9ede3', borderRadius: '6px', px: .9, py: .3, color: '#5d6b54' }}>{query.data.length}</Box>}</Stack>
          <Typography sx={{ display: { xs: 'none', sm: 'block' }, fontSize: 12, color: 'text.secondary' }}>Selecione um caso para continuar</Typography>
        </Stack>
        <Paper elevation={0} sx={{ overflow: 'hidden', borderRadius: '18px' }}>
          <Stack direction={{ xs: 'column-reverse', md: 'row' }} alignItems={{ md: 'center' }} justifyContent="space-between" gap={2} sx={{ px: { xs: 2, sm: 3 }, pt: 2.5, pb: 2, borderBottom: '1px solid #edf0ea' }}>
            <Stack direction="row" gap={.5} sx={{ overflowX: 'auto', pb: .5 }} aria-label="Filtrar por situação">{filtersList.map(filter => <Button key={filter.value} size="small" aria-pressed={situacao === filter.value} onClick={() => setSituacao(filter.value)} sx={{ flexShrink: 0, whiteSpace: 'nowrap', fontSize: { xs: 11, sm: 12 }, minWidth: 0, minHeight: 36, px: 1, color: situacao === filter.value ? '#254c40' : '#738070', bgcolor: situacao === filter.value ? '#edf3e6' : 'transparent' }}>{filter.label}</Button>)}</Stack>
            <TextField size="small" placeholder="Buscar atendimento…" value={busca} onChange={e => setBusca(e.target.value)} sx={{ width: { xs: '100%', md: 230 } }} slotProps={{ htmlInput: { maxLength: 160, 'aria-label': 'Buscar pelo título' }, input: { startAdornment: <InputAdornment position="start"><Search size={16} /></InputAdornment>, endAdornment: busca ? <InputAdornment position="end"><IconButton size="small" aria-label="Limpar busca" onClick={() => setBusca('')}><X size={14} /></IconButton></InputAdornment> : undefined } }} />
          </Stack>
          {!enabled && <Alert severity="info" sx={{ m: 2 }}>Preparando seu espaço de trabalho…</Alert>}
          {query.isLoading && <Stack alignItems="center" sx={{ p: 5 }}><CircularProgress size={24} aria-label="Carregando atendimentos" /></Stack>}
          {query.isError && <Alert severity="error" sx={{ m: 2 }} action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não foi possível carregar os atendimentos.</Alert>}
          {query.isSuccess && query.data.length === 0 && <Stack alignItems="center" spacing={1.5} sx={{ py: 7, px: 3, textAlign: 'center' }}><FolderOpen size={32} strokeWidth={1.3} color="#8a9b80" /><Typography fontWeight={650}>{hasFilters ? 'Nenhum atendimento encontrado' : 'Seu primeiro atendimento começa aqui'}</Typography><Typography color="text.secondary" fontSize={13}>{hasFilters ? 'Experimente outro nome ou outra situação.' : 'Crie um caso para reunir os dados e os documentos.'}</Typography><Button onClick={() => { if (hasFilters) { setBusca(''); setTerm(''); setSituacao('') } else setCreating(true) }}>{hasFilters ? 'Limpar filtros' : 'Criar atendimento'}<ArrowRight size={15} style={{ marginLeft: 8 }} /></Button></Stack>}
          {query.data?.map(item => <CaseRow key={item.id} item={item} />)}
        </Paper>
      </Box>
      <Stack direction="row" gap={1} alignItems="center" sx={{ color: '#778272', pb: 1 }}><Check size={14} /><Typography sx={{ fontSize: 11 }}>Você confere e aprova cada informação antes de finalizar.</Typography></Stack>
    </Stack>
    {creating && <NovoAtendimento open={creating} onClose={() => setCreating(false)} />}
  </AtendimentoLayout>
}
