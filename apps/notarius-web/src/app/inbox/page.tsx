'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Processo } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { PageHeader } from '@/components/layout/PageHeader'
import { StatsCards } from '@/components/inbox/StatsCards'
import { ProcessTable } from '@/components/inbox/ProcessTable'
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  Paper,
  Typography,
} from '@mui/material'
import { Add as PlusIcon, Search as MagnifyingGlassIcon } from '@mui/icons-material'
import { useProcessos } from '@/hooks/api/useProcessos'
import { useDashboardSummary } from '@/hooks/api/useWorkflowTasks'

export default function InboxPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [tipoFilter, setTipoFilter] = useState<string>('')

  // Fetch data
  const { data: processosData, isLoading: processosLoading } = useProcessos({
    search: searchTerm || undefined,
    status: statusFilter || undefined,
    tipo_ato: tipoFilter || undefined,
    page_size: 20
  })


  const { data: dashboardStats, isLoading: statsLoading } = useDashboardSummary()

  const handleViewProcess = (processo: Processo) => {
    router.push(`/processos/${processo.id}`)
  }

  const handleUploadDocument = (processo: Processo) => {
    router.push(`/documentos?processo=${processo.id}`)
  }

  const handleEditProcess = (processo: Processo) => {
    router.push(`/processos/${processo.id}/edit`)
  }

  const handleCreateProcess = () => {
    router.push('/criar')
  }

  const handleClearFilters = () => {
    setSearchTerm('')
    setStatusFilter('')
    setTipoFilter('')
  }

  return (
    <MainLayout>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Page Header */}
        <PageHeader
          title="Inbox"
          description="Gerencie seus processos e acompanhe o progresso dos trabalhos"
        >
          <Button 
            onClick={handleCreateProcess} 
            variant="contained"
            startIcon={<PlusIcon />}
            sx={{
              background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1565c0, #1976d2)',
              },
            }}
          >
            Novo Processo
          </Button>
        </PageHeader>

        {/* Stats Cards */}
        <StatsCards stats={dashboardStats} />

        {/* Filters */}
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, alignItems: 'center' }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <TextField
                fullWidth
                placeholder="Buscar processos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <MagnifyingGlassIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            
            <Box sx={{ minWidth: { xs: '100%', md: '250px' } }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">Todos os status</MenuItem>
                  <MenuItem value="rascunho">Rascunho</MenuItem>
                  <MenuItem value="em_analise">Em Análise</MenuItem>
                  <MenuItem value="aprovado">Aprovado</MenuItem>
                  <MenuItem value="rejeitado">Rejeitado</MenuItem>
                  <MenuItem value="concluido">Concluído</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <Box sx={{ minWidth: { xs: '100%', md: '300px' } }}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Ato</InputLabel>
                <Select
                  value={tipoFilter}
                  label="Tipo de Ato"
                  onChange={(e) => setTipoFilter(e.target.value)}
                >
                  <MenuItem value="">Todos os tipos</MenuItem>
                  <MenuItem value="procuracao">Procuração</MenuItem>
                  <MenuItem value="escritura">Escritura</MenuItem>
                  <MenuItem value="autenticacao">Autenticação</MenuItem>
                  <MenuItem value="reconhecimento">Reconhecimento de Firma</MenuItem>
                  <MenuItem value="testamento">Testamento</MenuItem>
                  <MenuItem value="contrato">Contrato</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                onClick={handleClearFilters}
                disabled={!searchTerm && !statusFilter && !tipoFilter}
              >
                Limpar Filtros
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Process Table */}
        <Paper sx={{ overflow: 'hidden' }}>
          {processosLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    border: '3px solid',
                    borderColor: 'primary.light',
                    borderTopColor: 'primary.main',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    '@keyframes spin': {
                      '0%': { transform: 'rotate(0deg)' },
                      '100%': { transform: 'rotate(360deg)' },
                    },
                  }}
                />
                <Typography color="text.secondary">Carregando processos...</Typography>
              </Box>
            </Box>
          ) : (
            <ProcessTable
              processos={processosData?.results || []}
              onViewProcess={handleViewProcess}
              onUploadDocument={handleUploadDocument}
              onEditProcess={handleEditProcess}
            />
          )}
        </Paper>

        {/* Pagination */}
        {processosData && processosData.count > 20 && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Mostrando {processosData.results.length} de {processosData.count} processos
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="outlined" size="small" disabled>
                Anterior
              </Button>
              <Button variant="outlined" size="small" disabled>
                Próximo
              </Button>
            </Box>
          </Box>
        )}
      </Box>
    </MainLayout>
  )
}
