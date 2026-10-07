'use client'

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Chip,
  Button,
  IconButton,
  Box,
  Typography,
  Tooltip,
} from '@mui/material'
import {
  Visibility as EyeIcon,
  Description as DocumentTextIcon,
  Download as ArrowDownTrayIcon,
  Edit as PencilIcon,
  Delete as TrashIcon,
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

interface MinutaTableProps {
  minutas: Minuta[]
  onViewMinuta?: (minuta: Minuta) => void
  onEditMinuta?: (minuta: Minuta) => void
  onDeleteMinuta?: (minuta: Minuta) => void
  onGeneratePDF?: (minuta: Minuta) => void
  onDownloadPDF?: (minuta: Minuta) => void
}

export function MinutaTable({ 
  minutas, 
  onViewMinuta, 
  onEditMinuta, 
  onDeleteMinuta,
  onGeneratePDF,
  onDownloadPDF
}: MinutaTableProps) {
  const [sortField, setSortField] = useState<keyof Minuta>('data_atualizacao')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  const getOrigemIcon = (origem: string) => {
    switch (origem.toLowerCase()) {
      case 'ia':
        return <CpuChipIcon sx={{ fontSize: 16, color: 'primary.main' }} />
      case 'humano':
        return <UserIcon sx={{ fontSize: 16, color: 'success.main' }} />
      default:
        return <DocumentTextIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleSort = (field: keyof Minuta) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedMinutas = [...minutas].sort((a, b) => {
    const aValue = a[sortField]
    const bValue = b[sortField]
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  return (
    <Box>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('processo')}
            >
              Processo
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('versao')}
            >
              Versão
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('origem')}
            >
              Origem
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('data_criacao')}
            >
              Criado em
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('created_by')}
            >
              Autor
            </TableCell>
            <TableCell>PDF</TableCell>
            <TableCell sx={{ textAlign: 'right' }}>Ações</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedMinutas.map((minuta) => (
            <TableRow 
              key={minuta.id}
              sx={{ 
                cursor: 'pointer', 
                '&:hover': { backgroundColor: 'action.hover' } 
              }}
              onClick={() => onViewMinuta?.(minuta)}
            >
              <TableCell>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {minuta.processo.numero_protocolo || `#${minuta.processo.id.slice(-6)}`}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {minuta.processo.tipo_ato}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip 
                  label={`v${minuta.versao}`} 
                  variant="outlined" 
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  icon={getOrigemIcon(minuta.origem)}
                  label={minuta.origem}
                  color={getOrigemColor(minuta.origem) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {formatDate(minuta.data_criacao)}
                </Typography>
              </TableCell>
              <TableCell>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {minuta.created_by.first_name} {minuta.created_by.last_name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    @{minuta.created_by.username}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                {minuta.pdf_url ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip 
                      label="Disponível" 
                      color="success" 
                      variant="outlined" 
                      size="small"
                    />
                    <Tooltip title="Baixar PDF">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDownloadPDF?.(minuta)
                        }}
                      >
                        <ArrowDownTrayIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                ) : (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      onGeneratePDF?.(minuta)
                    }}
                  >
                    Gerar PDF
                  </Button>
                )}
              </TableCell>
              <TableCell sx={{ textAlign: 'right' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                  <Tooltip title="Visualizar">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        onViewMinuta?.(minuta)
                      }}
                    >
                      <EyeIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Editar">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        onEditMinuta?.(minuta)
                      }}
                    >
                      <PencilIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Excluir">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteMinuta?.(minuta)
                      }}
                      sx={{ color: 'error.main' }}
                    >
                      <TrashIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      {minutas.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <DocumentTextIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" component="h3" gutterBottom>
            Nenhuma minuta encontrada
          </Typography>
          <Typography color="text.secondary">
            Crie uma nova minuta ou ajuste os filtros de busca.
          </Typography>
        </Box>
      )}
    </Box>
  )
}
