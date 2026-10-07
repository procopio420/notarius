'use client'

import { useState, useEffect } from 'react'
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Grid,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Person as UserIcon,
  Description as DocumentTextIcon,
  Schedule as CalendarIcon,
  LocationOn as MapPinIcon,
  AutoAwesome as SparklesIcon,
} from '@mui/icons-material'
import { CircularProgress } from '@mui/material'

interface Party {
  name: string
  role: string
  cpf?: string
  email?: string
}

interface Metadata {
  validity_days?: number
  location?: string
  special_conditions?: string[]
}

interface ParsedIntent {
  document_type: string
  parties: Party[]
  metadata: Metadata
  confidence_score: number
}

interface AnalysisResultProps {
  parsedIntent: ParsedIntent
  onProceed: () => void
  onEdit: () => void
  isGenerating?: boolean
}

export function AnalysisResult({ parsedIntent, onProceed, onEdit, isGenerating = false }: AnalysisResultProps) {
  // Helper function to safely get party name as string
  const getPartyName = (party: Party): string => {
    if (!party || !party.name) return ''
    return String(party.name).trim()
  }

  const [selectedParties, setSelectedParties] = useState<Set<string>>(
    new Set((parsedIntent.parties || [])
      .filter(p => p && getPartyName(p))
      .map(p => getPartyName(p)))
  )

  // Update selectedParties when parsedIntent changes
  useEffect(() => {
    const validParties = (parsedIntent.parties || [])
      .filter(p => p && getPartyName(p))
      .map(p => getPartyName(p))
    setSelectedParties(new Set(validParties))
  }, [parsedIntent.parties])

  const toggleParty = (partyName: string) => {
    const newSelected = new Set(selectedParties)
    if (newSelected.has(partyName)) {
      newSelected.delete(partyName)
    } else {
      newSelected.add(partyName)
    }
    setSelectedParties(newSelected)
  }

  const getRoleColor = (role: string) => {
    switch (role?.toLowerCase() || 'geral') {
      case 'outorgante':
        return 'primary'
      case 'outorgado':
        return 'success'
      case 'testemunha':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getRoleLabel = (role: string) => {
    switch (role?.toLowerCase() || 'geral') {
      case 'outorgante':
        return 'Outorgante'
      case 'outorgado':
        return 'Outorgado'
      case 'testemunha':
        return 'Testemunha'
      default:
        return role || 'Parte'
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
            ✅ Análise Concluída
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Confiança: {Math.round((parsedIntent.confidence_score || 0) * 100)}%
          </Typography>
        </Box>
        <Chip
          label={(parsedIntent.confidence_score || 0) > 0.8 ? 'Alta confiança' : 'Confiança média'}
          color={(parsedIntent.confidence_score || 0) > 0.8 ? 'success' : 'warning'}
          size="small"
        />
      </Box>

      {/* Document Type - Prominent Display */}
      <Card sx={{ border: 2, borderColor: 'primary.main', bgcolor: 'primary.50' }}>
        <CardContent sx={{ textAlign: 'center', py: 3 }}>
          <DocumentTextIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main', mb: 1 }}>
            {parsedIntent.document_type || 'Tipo de Documento'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Tipo de documento identificado pela IA
          </Typography>
        </CardContent>
      </Card>

      {/* Parties - Clear and Interactive */}
      {parsedIntent.parties && parsedIntent.parties.length > 0 ? (
        <Card>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <UserIcon />
              Partes Identificadas ({parsedIntent.parties.length})
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Clique para incluir/excluir cada parte do processo
            </Typography>
          </CardHeader>
          <CardContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {parsedIntent.parties.map((party, index) => {
                const partyName = getPartyName(party)
                return (
                <Box
                  key={index}
                  sx={{
                    p: 3,
                    border: 2,
                    borderColor: selectedParties.has(partyName) ? 'success.main' : 'grey.300',
                    borderRadius: 2,
                    cursor: 'pointer',
                    bgcolor: selectedParties.has(partyName) ? 'success.50' : 'grey.50',
                    '&:hover': {
                      borderColor: selectedParties.has(partyName) ? 'success.dark' : 'primary.main',
                      bgcolor: selectedParties.has(partyName) ? 'success.100' : 'primary.50'
                    },
                    transition: 'all 0.2s',
                    position: 'relative'
                  }}
                  onClick={() => toggleParty(partyName)}
                >
                  {/* Selection Indicator */}
                  <Box sx={{ 
                    position: 'absolute', 
                    top: 8, 
                    right: 8,
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    bgcolor: selectedParties.has(partyName) ? 'success.main' : 'grey.400',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {selectedParties.has(partyName) && (
                      <CheckCircleIcon sx={{ fontSize: 16, color: 'white' }} />
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ 
                      width: 48, 
                      height: 48, 
                      borderRadius: '50%', 
                      bgcolor: getRoleColor(party.role) + '.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: 600
                    }}>
                      {String(partyName || '?').charAt(0).toUpperCase() || '?'}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {partyName || 'Nome não informado'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {party.cpf && `CPF: ${party.cpf}`}
                        {party.email && ` • ${party.email}`}
                        {!party.cpf && !party.email && 'Informações adicionais não disponíveis'}
                      </Typography>
                      <Chip
                        label={getRoleLabel(party.role)}
                        color={getRoleColor(party.role) as any}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                </Box>
                )
              })}
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Card sx={{ border: 2, borderColor: 'warning.main', bgcolor: 'warning.50' }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <UserIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'warning.main', mb: 1 }}>
              Nenhuma parte identificada
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              A IA não conseguiu identificar partes específicas no texto. Tente ser mais específico sobre as pessoas envolvidas.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Exemplo: "Outorgante: João da Silva, CPF 123.456.789-00; Outorgado: Maria Souza, CPF 987.654.321-00"
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Additional Details */}
      {(parsedIntent.metadata.validity_days || parsedIntent.metadata.location || parsedIntent.metadata.special_conditions) && (
        <Card>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CalendarIcon />
              Detalhes Adicionais
            </Typography>
          </CardHeader>
          <CardContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {parsedIntent.metadata.validity_days && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                  <CalendarIcon sx={{ color: 'info.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">Validade</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {parsedIntent.metadata.validity_days} dias
                    </Typography>
                  </Box>
                </Box>
              )}
              {parsedIntent.metadata.location && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                  <MapPinIcon sx={{ color: 'info.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">Local</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {parsedIntent.metadata.location}
                    </Typography>
                  </Box>
                </Box>
              )}
              {parsedIntent.metadata.special_conditions && parsedIntent.metadata.special_conditions.length > 0 && (
                <Box sx={{ p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Condições especiais:
                  </Typography>
                  {parsedIntent.metadata.special_conditions.map((condition, index) => (
                    <Typography key={index} variant="body2" sx={{ ml: 2, mb: 0.5 }}>
                      • {condition}
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <Card sx={{ bgcolor: 'grey.50' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            📋 Resumo da Análise
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="body2">
              • <strong>Tipo:</strong> {parsedIntent.document_type || 'Não identificado'}
            </Typography>
            <Typography variant="body2">
              • <strong>Partes:</strong> {selectedParties.size} de {(parsedIntent.parties || []).filter(p => p && getPartyName(p)).length} selecionadas
            </Typography>
            <Typography variant="body2">
              • <strong>Confiança:</strong> {Math.round((parsedIntent.confidence_score || 0) * 100)}%
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Actions */}
      <Box sx={{ display: 'flex', gap: 2, pt: 2 }}>
        <Button
          variant="contained"
          onClick={onProceed}
          startIcon={isGenerating ? <CircularProgress size={16} color="inherit" /> : <SparklesIcon />}
          sx={{ 
            flex: 1,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            background: isGenerating 
              ? 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)'
              : 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1565c0 30%, #1976d2 90%)',
            }
          }}
          disabled={selectedParties.size === 0 || isGenerating}
        >
          {isGenerating ? 'Gerando Documento...' : `Criar Processo (${selectedParties.size} partes)`}
        </Button>
        <Button 
          variant="outlined" 
          onClick={onEdit}
          sx={{ py: 1.5 }}
        >
          ✏️ Editar
        </Button>
      </Box>
    </Box>
  )
}

