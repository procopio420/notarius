'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Paper,
  IconButton,
  CircularProgress,
  Alert,
  Chip,
  Divider
} from '@mui/material'
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  Edit as EditIcon
} from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'

interface DocumentViewerProps {
  open: boolean
  onClose: () => void
  document: {
    id: string
    versao: number
    corpo_md: string
    variaveis_json: Record<string, unknown>
  }
  processo: {
    id: string
    tipo_ato: string
    status: string
  }
  aiGeneration: {
    id: string
    confidence_score: number
    generation_time_ms: number
  }
  onEdit?: () => void
  onDownload?: () => void
}

export function DocumentViewer({
  open,
  onClose,
  document,
  processo,
  aiGeneration,
  onEdit,
  onDownload
}: DocumentViewerProps) {
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false)

  const handleDownload = async () => {
    setIsGeneratingPDF(true)
    try {
      const token = localStorage.getItem('auth_token')
      const tenantId = localStorage.getItem('tenant_id')
      if (!token || !tenantId) {
        throw new Error('Authentication required')
      }

      // First, approve the minuta
      const approveResponse = await fetch(`http://localhost:8000/api/v1/ai/approve-minuta/${document.id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
          'X-Tenant-ID': tenantId || ''
        }
      })

      if (!approveResponse.ok) {
        const error = await approveResponse.json()
        throw new Error(error.detail || 'Approve failed')
      }

      // Then, finalize the minuta
      const response = await fetch(`http://localhost:8000/api/v1/ai/finalize-minuta/${document.id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
          'X-Tenant-ID': tenantId || ''
        }
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'PDF generation failed')
      }
      
      // Check if response is JSON or PDF
      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/pdf')) {
        // Direct PDF response
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${document.tipo || 'documento'}-${document.id}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        // JSON response with S3 URL
        const data = await response.json()
        if (data.documento?.s3_key || data.documento?.url) {
          window.open(data.documento.url || data.documento.s3_key, '_blank')
        }
      }
      
      onDownload?.()
    } catch (error) {
      console.error('PDF generation failed:', error)
      alert(`Failed to generate PDF: ${error.message}. Please try again.`)
    } finally {
      setIsGeneratingPDF(false)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: `Documento - ${processo.tipo_ato}`,
        text: `Documento gerado automaticamente pelo sistema Notarius`,
        url: window.location.href
      })
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href)
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
          maxHeight: '90vh'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        borderBottom: 1,
        borderColor: 'divider'
      }}>
        <Box>
          <Typography variant="h6" component="div">
            Documento Gerado
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {processo.tipo_ato} • Versão {document.versao}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0, overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', height: '100%' }}>
          {/* Document Content */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
            <Paper 
              elevation={1} 
              sx={{ 
                p: 4, 
                minHeight: '100%',
                backgroundColor: 'background.paper',
                '& h1, & h2, & h3, & h4, & h5, & h6': {
                  color: 'primary.main',
                  fontWeight: 600,
                  mb: 2
                },
                '& p': {
                  mb: 2,
                  lineHeight: 1.6
                },
                '& strong': {
                  fontWeight: 600
                },
                '& ul, & ol': {
                  pl: 3,
                  mb: 2
                },
                '& li': {
                  mb: 1
                }
              }}
            >
              <ReactMarkdown>{document.corpo_md}</ReactMarkdown>
            </Paper>
          </Box>

          {/* Sidebar with metadata */}
          <Box sx={{ 
            width: 300, 
            borderLeft: 1, 
            borderColor: 'divider',
            p: 2,
            backgroundColor: 'grey.50',
            overflow: 'auto'
          }}>
            <Typography variant="h6" gutterBottom>
              Informações do Documento
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Processo
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                ID: {processo.id}
              </Typography>
              <Chip 
                label={processo.status} 
                size="small" 
                color="primary" 
                variant="outlined"
              />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Geração por IA
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Confiança: {(aiGeneration.confidence_score * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Tempo: {aiGeneration.generation_time_ms}ms
              </Typography>
              <Chip 
                label="IA Gerado" 
                size="small" 
                color="success" 
                variant="outlined"
              />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Variáveis
              </Typography>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                <pre style={{ 
                  fontSize: '0.75rem', 
                  backgroundColor: 'rgba(0,0,0,0.05)', 
                  padding: '8px', 
                  borderRadius: '4px',
                  margin: 0
                }}>
                  {JSON.stringify(document.variaveis_json, null, 2)}
                </pre>
              </Box>
            </Box>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ 
        borderTop: 1, 
        borderColor: 'divider',
        p: 2,
        gap: 1
      }}>
        <Button
          variant="outlined"
          startIcon={<ShareIcon />}
          onClick={handleShare}
        >
          Compartilhar
        </Button>
        
        <Button
          variant="outlined"
          startIcon={<PrintIcon />}
          onClick={handlePrint}
        >
          Imprimir
        </Button>
        
        <Button
          variant="outlined"
          startIcon={isGeneratingPDF ? <CircularProgress size={16} /> : <DownloadIcon />}
          onClick={handleDownload}
          disabled={isGeneratingPDF}
        >
          {isGeneratingPDF ? 'Gerando PDF...' : 'Baixar PDF'}
        </Button>
        
        {onEdit && (
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={onEdit}
          >
            Editar
          </Button>
        )}
        
        <Button
          variant="contained"
          onClick={onClose}
          sx={{
            background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1565c0 30%, #1976d2 90%)',
            }
          }}
        >
          Fechar
        </Button>
      </DialogActions>
    </Dialog>
  )
}

