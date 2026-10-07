'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Chip,
  Tabs,
  Tab,
  Box,
  Typography,
  Divider,
  IconButton,
} from '@mui/material'
import {
  Download as ArrowDownTrayIcon,
  Edit as PencilIcon,
  Check as CheckIcon,
  Close as XMarkIcon,
  SmartToy as CpuChipIcon,
  Person as UserIcon,
} from '@mui/icons-material'

interface Minuta {
  id: string
  versao: number
  corpo_md: string
  variaveis_json: Record<string, unknown>
  origem: string
  data_criacao: string
  data_atualizacao: string
  created_by: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  processo: {
    id: string
    tipo_ato: string
    numero_protocolo?: string
  }
  template?: {
    id: string
    nome: string
    versao: number
  }
  pdf_url?: string
  pdf_generated_at?: string
}

interface MinutaDetailDialogProps {
  minuta: Minuta | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onEdit?: (minuta: Minuta) => void
  onGeneratePDF?: (minuta: Minuta) => void
  onDownloadPDF?: (minuta: Minuta) => void
}

export function MinutaDetailDialog({
  minuta,
  open,
  onOpenChange,
  onEdit,
  onGeneratePDF,
  onDownloadPDF
}: MinutaDetailDialogProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [tabValue, setTabValue] = useState(0)

  if (!minuta) return null

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getOrigemIcon = (origem: string) => {
    switch (origem.toLowerCase()) {
      case 'ia':
        return <CpuChipIcon sx={{ fontSize: 16, color: 'primary.main' }} />
      case 'humano':
        return <UserIcon sx={{ fontSize: 16, color: 'success.main' }} />
      default:
        return <UserIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
    }
  }

  const getOrigemColor = (origem: string) => {
    switch (origem.toLowerCase()) {
      case 'ia':
        return 'primary'
      case 'humano':
        return 'success'
      default:
        return 'default'
    }
  }

  const handleEdit = () => {
    setEditedContent(minuta.corpo_md)
    setIsEditing(true)
  }

  const handleSave = () => {
    // This would call the update mutation
    setIsEditing(false)
    onEdit?.(minuta)
  }

  const handleCancel = () => {
    setEditedContent('')
    setIsEditing(false)
  }

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering - in a real app you'd use a proper markdown library
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
  }

  return (
    <Dialog 
      open={open} 
      onClose={() => onOpenChange(false)}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="div">
              Minuta v{minuta.versao}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {minuta.processo.tipo_ato} • {minuta.processo.numero_protocolo || `#${minuta.processo.id.slice(-6)}`}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              icon={getOrigemIcon(minuta.origem)}
              label={minuta.origem}
              color={getOrigemColor(minuta.origem) as any}
              size="small"
            />
            {minuta.pdf_url ? (
              <Button
                variant="outlined"
                size="small"
                startIcon={<ArrowDownTrayIcon />}
                onClick={() => onDownloadPDF?.(minuta)}
              >
                Baixar PDF
              </Button>
            ) : (
              <Button
                variant="outlined"
                size="small"
                onClick={() => onGeneratePDF?.(minuta)}
              >
                Gerar PDF
              </Button>
            )}
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Conteúdo" />
            <Tab label="Variáveis" />
            <Tab label="Informações" />
          </Tabs>
        </Box>

        <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
          {tabValue === 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">Conteúdo da Minuta</Typography>
                {!isEditing ? (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<PencilIcon />}
                    onClick={handleEdit}
                  >
                    Editar
                  </Button>
                ) : (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<XMarkIcon />}
                      onClick={handleCancel}
                    >
                      Cancelar
                    </Button>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<CheckIcon />}
                      onClick={handleSave}
                    >
                      Salvar
                    </Button>
                  </Box>
                )}
              </Box>

              {isEditing ? (
                <TextField
                  multiline
                  fullWidth
                  rows={20}
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  placeholder="Digite o conteúdo da minuta em Markdown..."
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '0.875rem'
                    }
                  }}
                />
              ) : (
                <Box
                  sx={{
                    p: 2,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    bgcolor: 'grey.50',
                    minHeight: 400,
                    '& p': { margin: '0 0 1rem 0' },
                    '& strong': { fontWeight: 600 },
                    '& em': { fontStyle: 'italic' }
                  }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(minuta.corpo_md) }}
                />
              )}
            </Box>
          )}

          {tabValue === 1 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography variant="h6">Variáveis</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                {Object.entries(minuta.variaveis_json).map(([key, value]) => (
                  <Box key={key} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                      {key}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.5 }}>
                      {typeof value === 'string' ? value : JSON.stringify(value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          {tabValue === 2 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography variant="h6">Informações</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Criado em:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {formatDate(minuta.data_criacao)}
                  </Typography>
                </Box>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Atualizado em:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {formatDate(minuta.data_atualizacao)}
                  </Typography>
                </Box>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Autor:</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {minuta.created_by.first_name} {minuta.created_by.last_name}
                  </Typography>
                </Box>
                {minuta.template && (
                  <>
                    <Divider />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Template:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {minuta.template.nome} v{minuta.template.versao}
                      </Typography>
                    </Box>
                  </>
                )}
                {minuta.pdf_generated_at && (
                  <>
                    <Divider />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">PDF gerado em:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {formatDate(minuta.pdf_generated_at)}
                      </Typography>
                    </Box>
                  </>
                )}
              </Box>
            </Box>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  )
}
