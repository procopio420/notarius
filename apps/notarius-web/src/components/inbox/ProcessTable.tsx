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
  CloudUpload as CloudArrowUpIcon,
  Edit as PencilIcon,
  Description as DocumentTextIcon,
} from '@mui/icons-material'

interface Processo {
  id: string
  tipo_ato: string
  status: string
  numero_protocolo?: string
  data_criacao: string
  data_atualizacao: string
  responsavel?: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  partes_count: number
  documentos_count: number
  minutas_count: number
}

interface ProcessTableProps {
  processos: Processo[]
  onViewProcess?: (processo: Processo) => void
  onUploadDocument?: (processo: Processo) => void
  onEditProcess?: (processo: Processo) => void
}

export function ProcessTable({ 
  processos, 
  onViewProcess, 
  onUploadDocument, 
  onEditProcess 
}: ProcessTableProps) {
  const [sortField, setSortField] = useState<keyof Processo>('data_atualizacao')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'rascunho':
        return 'primary'
      case 'em_analise':
        return 'warning'
      case 'aprovado':
        return 'success'
      case 'rejeitado':
        return 'error'
      case 'concluido':
        return 'default'
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

  const handleSort = (field: keyof Processo) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedProcessos = [...processos].sort((a, b) => {
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
              onClick={() => handleSort('numero_protocolo')}
            >
              #
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('tipo_ato')}
            >
              Tipo
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('status')}
            >
              Status
            </TableCell>
            <TableCell 
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
              onClick={() => handleSort('data_atualizacao')}
            >
              Atualizado
            </TableCell>
            <TableCell>Responsável</TableCell>
            <TableCell sx={{ textAlign: 'right' }}>Ações</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedProcessos.map((processo) => (
            <TableRow 
              key={processo.id}
              sx={{ 
                cursor: 'pointer', 
                '&:hover': { backgroundColor: 'action.hover' } 
              }}
              onClick={() => onViewProcess?.(processo)}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {processo.numero_protocolo || `#${processo.id.slice(-6)}`}
                </Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DocumentTextIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
                  <Typography variant="body2">
                    {processo.tipo_ato}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  label={processo.status.replace('_', ' ')}
                  color={getStatusColor(processo.status) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {formatDate(processo.data_atualizacao)}
                </Typography>
              </TableCell>
              <TableCell>
                {processo.responsavel ? (
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {processo.responsavel.first_name} {processo.responsavel.last_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      @{processo.responsavel.username}
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.disabled">
                    Não atribuído
                  </Typography>
                )}
              </TableCell>
              <TableCell sx={{ textAlign: 'right' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                  <Tooltip title="Visualizar">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        onViewProcess?.(processo)
                      }}
                    >
                      <EyeIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Upload de Documento">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        onUploadDocument?.(processo)
                      }}
                    >
                      <CloudArrowUpIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Editar">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        onEditProcess?.(processo)
                      }}
                    >
                      <PencilIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      {processos.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <DocumentTextIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" component="h3" gutterBottom>
            Nenhum processo encontrado
          </Typography>
          <Typography color="text.secondary">
            Crie um novo processo ou ajuste os filtros de busca.
          </Typography>
        </Box>
      )}
    </Box>
  )
}
