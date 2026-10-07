'use client'

import { useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Documento } from '@/types'
import { MainLayout } from '@/components/layout/main-layout'
import { PageHeader } from '@/components/layout/PageHeader'
import { DocumentCard } from '@/components/documentos/DocumentCard'
import { DocumentFilters } from '@/components/documentos/DocumentFilters'
import { UploadDialog } from '@/components/documentos/UploadDialog'
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  CircularProgress,
} from '@mui/material'
import { CloudUpload as CloudArrowUpIcon, Description as DocumentIcon } from '@mui/icons-material'
import { useDocumentos, useDownloadDocumento, useDeleteDocumento } from '@/hooks/api/useDocumentos'

export default function DocumentosPage() {
  const searchParams = useSearchParams()
  const processoId = searchParams.get('processo')
  
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [tipoFilter, setTipoFilter] = useState('')
  const [processoFilter, setProcessoFilter] = useState(processoId || '')

  // Fetch data
  const { data: documentosData, isLoading } = useDocumentos({
    search: searchTerm || undefined,
    status_ocr: statusFilter || undefined,
    tipo: tipoFilter || undefined,
    processo_id: processoFilter || undefined,
    page_size: 20
  })

  const downloadMutation = useDownloadDocumento()
  const deleteMutation = useDeleteDocumento()

  const handleViewDocument = (documento: Documento) => {
    // Open document in new tab
    window.open(documento.url_arquivo, '_blank')
  }

  const handleDownloadDocument = async (documento: Documento) => {
    try {
      const blob = await downloadMutation.mutateAsync(documento.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = documento.nome_arquivo
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const handleDeleteDocument = async (documento: Documento) => {
    if (confirm(`Tem certeza que deseja excluir o documento "${documento.nome_arquivo}"?`)) {
      try {
        await deleteMutation.mutateAsync(documento.id)
      } catch (error) {
        console.error('Delete failed:', error)
      }
    }
  }

  const handleUploadSuccess = () => {
    // The query will automatically refetch due to invalidation
  }

  return (
    <MainLayout>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Page Header */}
        <PageHeader
          title="Documentos"
          description="Gerencie documentos e acompanhe o processamento OCR"
        >
          <UploadDialog onSuccess={handleUploadSuccess}>
            <Button 
              variant="contained"
              startIcon={<CloudArrowUpIcon />}
              sx={{
                background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #1565c0, #1976d2)',
                },
              }}
            >
              Upload Documentos
            </Button>
          </UploadDialog>
        </PageHeader>

        {/* Filters */}
        <DocumentFilters
          search={searchTerm}
          onSearchChange={setSearchTerm}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          tipoFilter={tipoFilter}
          onTipoChange={setTipoFilter}
          processoFilter={processoFilter}
          onProcessoChange={setProcessoFilter}
        />

        {/* Documents Grid */}
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={32} />
              <Typography color="text.secondary">Carregando documentos...</Typography>
            </Box>
          </Box>
        ) : documentosData?.results && documentosData.results.length > 0 ? (
          <Grid container spacing={3}>
            {documentosData.results.map((documento) => (
              <Grid item xs={12} sm={6} lg={4} key={documento.id}>
                <DocumentCard
                  documento={documento}
                  onView={handleViewDocument}
                  onDownload={handleDownloadDocument}
                  onDelete={handleDeleteDocument}
                />
              </Grid>
            ))}
          </Grid>
        ) : (
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <DocumentIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" component="h3" gutterBottom>
              Nenhum documento encontrado
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              Faça upload de documentos ou ajuste os filtros de busca.
            </Typography>
            <UploadDialog onSuccess={handleUploadSuccess}>
              <Button 
                variant="contained"
                startIcon={<CloudArrowUpIcon />}
                sx={{
                  background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #1565c0, #1976d2)',
                  },
                }}
              >
                Fazer Upload
              </Button>
            </UploadDialog>
          </Paper>
        )}

        {/* Pagination */}
        {documentosData && documentosData.count > 20 && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Mostrando {documentosData.results.length} de {documentosData.count} documentos
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
