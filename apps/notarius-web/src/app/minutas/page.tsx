'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/main-layout'
import { PageHeader } from '@/components/layout/PageHeader'
import { MinutaTable } from '@/components/minutas/MinutaTable'
import { MinutaDetailDialog } from '@/components/minutas/MinutaDetailDialog'
import { useMinutas, useGeneratePDF, useDownloadPDF, useDeleteMinuta } from '@/hooks/api/useMinutas'
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Typography,
  CircularProgress,
  Button,
  InputAdornment,
} from '@mui/material'
import { Search as SearchIcon, Description as DocumentIcon } from '@mui/icons-material'

export default function MinutasPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [origemFilter, setOrigemFilter] = useState('')
  const [selectedMinuta, setSelectedMinuta] = useState<any>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)

  // Fetch data
  const { data: minutasData, isLoading } = useMinutas({
    search: searchTerm || undefined,
    origem: origemFilter || undefined,
    page_size: 20
  })

  const generatePDFMutation = useGeneratePDF()
  const downloadPDFMutation = useDownloadPDF()
  const deleteMinutaMutation = useDeleteMinuta()

  const handleViewMinuta = (minuta: any) => {
    setSelectedMinuta(minuta)
    setDetailDialogOpen(true)
  }

  const handleEditMinuta = (minuta: any) => {
    // This would open an edit dialog or navigate to edit page
    console.log('Edit minuta:', minuta)
  }

  const handleDeleteMinuta = async (minuta: any) => {
    if (confirm(`Tem certeza que deseja excluir a minuta v${minuta.versao}?`)) {
      try {
        await deleteMinutaMutation.mutateAsync(minuta.id)
      } catch (error) {
        console.error('Delete failed:', error)
      }
    }
  }

  const handleGeneratePDF = async (minuta: any) => {
    try {
      await generatePDFMutation.mutateAsync(minuta.id)
    } catch (error) {
      console.error('Generate PDF failed:', error)
    }
  }

  const handleDownloadPDF = async (minuta: any) => {
    try {
      const blob = await downloadPDFMutation.mutateAsync(minuta.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `minuta-${minuta.id}-v${minuta.versao}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download PDF failed:', error)
    }
  }

  return (
    <MainLayout>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Page Header */}
        <PageHeader
          title="Minutas"
          description="Gerencie minutas e gere documentos PDF"
        />

        {/* Filters */}
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, alignItems: 'center' }}>
            <Box sx={{ flex: 1 }}>
              <TextField
                fullWidth
                placeholder="Buscar minutas..."
                value={searchTerm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            
            <Box sx={{ minWidth: { xs: '100%', md: '200px' } }}>
              <FormControl fullWidth>
                <InputLabel>Origem</InputLabel>
                <Select
                  value={origemFilter}
                  label="Origem"
                  onChange={(e) => setOrigemFilter(e.target.value)}
                >
                  <MenuItem value="">Todas as origens</MenuItem>
                  <MenuItem value="ia">IA</MenuItem>
                  <MenuItem value="humano">Humano</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        </Paper>

        {/* Minutas Table */}
        <Paper sx={{ overflow: 'hidden' }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CircularProgress size={32} />
                <Typography color="text.secondary">Carregando minutas...</Typography>
              </Box>
            </Box>
          ) : (
            <MinutaTable
              minutas={minutasData?.results || []}
              onViewMinuta={handleViewMinuta}
              onEditMinuta={handleEditMinuta}
              onDeleteMinuta={handleDeleteMinuta}
              onGeneratePDF={handleGeneratePDF}
              onDownloadPDF={handleDownloadPDF}
            />
          )}
        </Paper>

        {/* Pagination */}
        {minutasData && minutasData.count > 20 && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Mostrando {minutasData.results.length} de {minutasData.count} minutas
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

        {/* Detail Dialog */}
        <MinutaDetailDialog
          minuta={selectedMinuta}
          open={detailDialogOpen}
          onOpenChange={setDetailDialogOpen}
          onEdit={handleEditMinuta}
          onGeneratePDF={handleGeneratePDF}
          onDownloadPDF={handleDownloadPDF}
        />
      </Box>
    </MainLayout>
  )
}
