'use client'

import { useState } from 'react'
import { Card, CardContent, Chip, Button, Box, Typography, IconButton } from '@mui/material'
import { 
  Description as DocumentIcon, 
  Visibility as EyeIcon, 
  Download as ArrowDownTrayIcon, 
  Delete as TrashIcon,
  Schedule as ClockIcon,
  CheckCircle as CheckCircleIcon,
  Warning as ExclamationTriangleIcon
} from '@mui/icons-material'

interface Documento {
  id: string
  tipo: string
  nome_arquivo: string
  tamanho_bytes: number
  mime_type: string
  url_arquivo: string
  status_ocr: string
  data_upload: string
  data_atualizacao: string
  uploaded_by: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  processo?: {
    id: string
    tipo_ato: string
    numero_protocolo?: string
  }
  ocr_text?: string
  ocr_confidence?: number
}

interface DocumentCardProps {
  documento: Documento
  onView?: (documento: Documento) => void
  onDownload?: (documento: Documento) => void
  onDelete?: (documento: Documento) => void
}

export function DocumentCard({ documento, onView, onDownload, onDelete }: DocumentCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'concluido':
        return <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
      case 'processando':
        return <ClockIcon sx={{ fontSize: 16, color: 'warning.main' }} />
      case 'erro':
        return <ExclamationTriangleIcon sx={{ fontSize: 16, color: 'error.main' }} />
      default:
        return <ClockIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'concluido':
        return 'success'
      case 'processando':
        return 'warning'
      case 'erro':
        return 'error'
      default:
        return 'default'
    }
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) {
      return '📄'
    } else if (mimeType.includes('image')) {
      return '🖼️'
    } else if (mimeType.includes('word') || mimeType.includes('document')) {
      return '📝'
    } else {
      return '📎'
    }
  }

  return (
    <Card 
      sx={{
        transition: 'all 0.2s',
        '&:hover': {
          boxShadow: 4
        },
        ...(isHovered && {
          border: 2,
          borderColor: 'primary.main'
        })
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1, minWidth: 0 }}>
            <Typography sx={{ fontSize: '1.5rem' }}>
              {getFileIcon(documento.mime_type)}
            </Typography>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {documento.nome_arquivo}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatFileSize(documento.tamanho_bytes)} • {formatDate(documento.data_upload)}
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={getStatusIcon(documento.status_ocr)}
              label={documento.status_ocr}
              color={getStatusColor(documento.status_ocr) as any}
              size="small"
            />
          </Box>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Tipo:</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>{documento.tipo}</Typography>
          </Box>
          
          {documento.processo && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Processo:</Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {documento.processo.numero_protocolo || `#${documento.processo.id.slice(-6)}`}
              </Typography>
            </Box>
          )}
          
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">Upload por:</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {documento.uploaded_by.first_name} {documento.uploaded_by.last_name}
            </Typography>
          </Box>

          {documento.ocr_confidence && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Confiança OCR:</Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {Math.round(documento.ocr_confidence * 100)}%
              </Typography>
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="text"
              size="small"
              onClick={() => onView?.(documento)}
              startIcon={<EyeIcon sx={{ fontSize: 16 }} />}
            >
              Ver
            </Button>
            <Button
              variant="text"
              size="small"
              onClick={() => onDownload?.(documento)}
              startIcon={<ArrowDownTrayIcon sx={{ fontSize: 16 }} />}
            >
              Baixar
            </Button>
          </Box>
          
          <IconButton
            size="small"
            onClick={() => onDelete?.(documento)}
            sx={{ color: 'error.main' }}
          >
            <TrashIcon sx={{ fontSize: 16 }} />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  )
}
