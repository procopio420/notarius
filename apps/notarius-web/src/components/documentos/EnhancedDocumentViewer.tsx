'use client'

import React, { useState, useEffect, useCallback } from 'react'
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
  Chip,
  Divider,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar
} from '@mui/material'
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  AutoAwesome as AIIcon
} from '@mui/icons-material'
import { useUpdateMinutaContent, useRewriteWithAI } from '../../hooks/api/useMinutas'
import { useAutoSave } from '../../hooks/useAutoSave'
import { RichTextEditor } from '../editor/RichTextEditor'
import { VariableInput } from './VariableInput'
import {
  extractVariablesFromDocument,
  updateVariableValues,
  replaceVariableInDocument,
  toggleVariableDisplay,
  formatVariableValue,
  parseVariableValue,
  validateVariableValue,
  DocumentVariable
} from '../../utils/documentVariables'

interface Minuta {
  id: string
  versao: number
  corpo_md: string
  variaveis_json: Record<string, unknown>
  status: string
  gerada_por: string
  processo: {
    id: string
    tipo_ato: string
    numero_protocolo?: string
  }
  created_by: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  created_at: string
  updated_at: string
  citations?: unknown[]
  grounding_confidence?: number
}

interface EnhancedDocumentViewerProps {
  open: boolean
  onClose: () => void
  minuta: Minuta
  onShare?: () => void
  onPrint?: () => void
  onDownloadPDF?: () => void
}

export function EnhancedDocumentViewer({
  open,
  onClose,
  minuta,
  onShare,
  onPrint,
  onDownloadPDF
}: EnhancedDocumentViewerProps) {
  // State
  const [documentContent, setDocumentContent] = useState(minuta.corpo_md || '')
  const [variables, setVariables] = useState<DocumentVariable[]>([])
  const [showRealValues, setShowRealValues] = useState(false) // Start with placeholders
  const [improvementPrompt, setImprovementPrompt] = useState('')
  const [selectedText, setSelectedText] = useState('')
  const [isEditing, setIsEditing] = useState(true)
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarMessage, setSnackbarMessage] = useState('')

  // API hooks
  const updateContentMutation = useUpdateMinutaContent()
  const rewriteWithAIMutation = useRewriteWithAI()

  // Initialize variables from document
  useEffect(() => {
    console.log('Initializing variables from document:', minuta.corpo_md)
    
    // Ensure corpo_md is a string (handle undefined/null)
    const initialContent = minuta.corpo_md || ''
    
    // First, update the document content to use separate placeholders for OUTORGANTE and OUTORGADO
    let updatedContent = initialContent
    
    // Replace generic placeholders with specific ones for OUTORGANTE and OUTORGADO
    updatedContent = updatedContent.replace(
      /OUTORGANTE.*?CPF n° \{\{PLACEHOLDER_CPF\}\}/g,
      'OUTORGANTE: {{OUTORGANTE}}, brasileiro, estado civil [informar], profissão [informar], portador da cédula de identidade nº {{RG_OUTORGANTE}} e do CPF nº {{CPF_OUTORGANTE}}, residente e domiciliado à [informar endereço completo]'
    )
    
    updatedContent = updatedContent.replace(
      /OUTORGADO.*?CPF n° \{\{PLACEHOLDER_CPF\}\}/g,
      'OUTORGADO: {{OUTORGADO}}, brasileira, estado civil [informar], profissão [informar], portadora da cédula de identidade nº {{RG_OUTORGADO}} e do CPF nº {{CPF_OUTORGADO}}, residente e domiciliada à [informar endereço completo]'
    )
    
    // Replace all PLACEHOLDER_ prefixes with cleaner names
    updatedContent = updatedContent.replace(/\{\{PLACEHOLDER_/g, '{{')
    updatedContent = updatedContent.replace(/\{\{PLACEHOLDER/g, '{{')
    
    // Fix specific placeholder mismatches to match the variables
    updatedContent = updatedContent.replace(/\{\{RG\}\}/g, '{{RG_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{CPF\}\}/g, '{{CPF_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{ENDERECO\}\}/g, '{{ENDERECO_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{NUMERO\}\}/g, '{{NUMERO_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{BAIRRO\}\}/g, '{{BAIRRO_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{CIDADE\}\}/g, '{{CIDADE_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{ESTADO\}\}/g, '{{ESTADO_OUTORGANTE}}')
    updatedContent = updatedContent.replace(/\{\{DATA\}\}/g, '{{DATA}}')
    updatedContent = updatedContent.replace(/\{\{DESCRICAO_IMOVEL\}\}/g, '{{OBJETO}}')
    
    // If the document doesn't have placeholders, create them from real values
    // This handles the case where the document already has real values
    if (!updatedContent.includes('{{')) {
      console.log('Document has no placeholders, creating them from real values')
      
      // Create a template with placeholders based on common patterns
      updatedContent = updatedContent
        .replace(/(OUTORGANTE:?\s*)([^,]+)/g, '$1{{OUTORGANTE}}')
        .replace(/(OUTORGADO:?\s*)([^,]+)/g, '$1{{OUTORGADO}}')
        .replace(/(CPF n[°º]\s*)(\d{3}\.\d{3}\.\d{3}-\d{2})/g, '$1{{CPF_OUTORGANTE}}')
        .replace(/(RG n[°º]\s*)(\d+)/g, '$1{{RG_OUTORGANTE}}')
        .replace(/(residente e domiciliado à\s*)([^,]+)/g, '$1{{ENDERECO_OUTORGANTE}}')
        .replace(/(residente e domiciliada à\s*)([^,]+)/g, '$1{{ENDERECO_OUTORGADO}}')
        .replace(/(objeto\s*)([^,]+)/gi, '$1{{OBJETO}}')
        .replace(/(prazo\s*)([^,]+)/gi, '$1{{PRAZO}}')
        .replace(/(data\s*)(\d{2}\/\d{2}\/\d{4})/gi, '$1{{DATA}}')
    }
    
    // Update document content if it changed
    if (updatedContent !== initialContent) {
      console.log('Updated document content with placeholders:', updatedContent)
      setDocumentContent(updatedContent)
    }
    
    const extractedVars = extractVariablesFromDocument(updatedContent || '')
    console.log('Extracted variables:', extractedVars)
    
    const varsWithValues = updateVariableValues(extractedVars, minuta.variaveis_json)
    console.log('Variables with values from JSON:', varsWithValues)
    
    // For demo purposes, add some sample real values
    const sampleValues: Record<string, string> = {
      'OUTORGANTE': 'João Silva Santos',
      'OUTORGADO': 'Maria Oliveira Costa',
      'ID': '12.345.678-9',
      'CPF_OUTORGANTE': '123.456.789-00',
      'CPF_OUTORGADO': '987.654.321-00',
      'RG_OUTORGANTE': '12.345.678-9',
      'RG_OUTORGADO': '98.765.432-1',
      'ENDERECO_OUTORGANTE': 'Rua das Flores',
      'ENDERECO_OUTORGADO': 'Avenida Principal',
      'NUMERO_OUTORGANTE': '123',
      'NUMERO_OUTORGADO': '456',
      'BAIRRO_OUTORGANTE': 'Centro',
      'BAIRRO_OUTORGADO': 'Vila Nova',
      'CIDADE_OUTORGANTE': 'São Paulo',
      'CIDADE_OUTORGADO': 'Rio de Janeiro',
      'ESTADO_OUTORGANTE': 'SP',
      'ESTADO_OUTORGADO': 'RJ',
      'CEP': '01234-567',
      'OBJETO': 'Venda de imóvel residencial',
      'PRAZO': '90 dias',
      'MATRICULA': '12345',
      'DATA': '26/10/2025',
      'NOME_TESTEMUNHA_1': 'Ana Silva',
      'CPF_TESTEMUNHA_1': '111.222.333-44',
      'NOME_TESTEMUNHA_2': 'Pedro Costa',
      'CPF_TESTEMUNHA_2': '555.666.777-88'
    }
    
    const varsWithRealValues = varsWithValues.map(variable => {
      // Always add sample values if the variable doesn't have a value
      const sampleValue = sampleValues[variable.name] || ''
      return {
        ...variable,
        value: variable.value || sampleValue
      }
    })
    
    console.log('Final variables with sample values:', varsWithRealValues)
    
    setVariables(varsWithRealValues)
  }, [minuta.corpo_md, minuta.variaveis_json, showRealValues])

  // Auto-save hook
  const { isSaving, lastSaved, error: saveError, hasUnsavedChanges } = useAutoSave(
    { corpo_md: documentContent, variaveis_json: minuta.variaveis_json },
    {
      delay: 500,
      onSave: async (data) => {
        await updateContentMutation.mutateAsync({
          id: minuta.id,
          data
        })
      },
      onError: (error) => {
        console.error('Auto-save failed:', error)
        setSnackbarMessage(`Erro ao salvar: ${error.message}`)
        setSnackbarOpen(true)
      },
      enabled: true
    }
  )

  // Handle document content changes
  const handleContentChange = useCallback((newContent: string) => {
    setDocumentContent(newContent)
    
    // Update variables if content changed
    const extractedVars = extractVariablesFromDocument(newContent)
    const varsWithValues = updateVariableValues(extractedVars, minuta.variaveis_json)
    setVariables(varsWithValues)
  }, [minuta.variaveis_json])

  // Handle variable value changes
  const handleVariableChange = useCallback((variableName: string, newValue: string) => {
    const parsedValue = parseVariableValue(variableName, newValue)
    
    // Update variables state
    setVariables(prev => prev.map(v => 
      v.name === variableName 
        ? { ...v, value: parsedValue }
        : v
    ))

    // Update document content
    const updatedContent = replaceVariableInDocument(documentContent, variableName, parsedValue)
    setDocumentContent(updatedContent)

    // Update variaveis_json
    const updatedVariaveisJson = {
      ...minuta.variaveis_json,
      [variableName]: parsedValue
    }
    minuta.variaveis_json = updatedVariaveisJson
  }, [documentContent, minuta])

  // Toggle variable display
  const toggleVariableDisplayMode = useCallback(() => {
    const newShowRealValues = !showRealValues
    setShowRealValues(newShowRealValues)
    
    console.log('Toggling variable display mode to:', newShowRealValues)
    console.log('Current variables:', variables)
    
    // Update document content to show real values or placeholders
    let updatedContent = documentContent || ''
    
    if (newShowRealValues) {
      // Replace placeholders with real values
      variables.forEach(variable => {
        if (variable.value && variable.placeholder) {
          const placeholder = String(variable.placeholder)
          const value = String(variable.value)
          console.log(`Replacing ${placeholder} with ${value}`)
          // Replace the placeholder with the real value
          try {
            const placeholderRegex = new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')
            const beforeReplace = updatedContent
            updatedContent = updatedContent.replace(placeholderRegex, value)
            if (beforeReplace !== updatedContent) {
              console.log(`✅ Successfully replaced ${placeholder}`)
            } else {
              console.log(`❌ No match found for ${placeholder}`)
            }
          } catch (error) {
            console.error(`Error replacing placeholder ${placeholder}:`, error)
          }
        }
      })
    } else {
      // Replace real values with placeholders
      variables.forEach(variable => {
        if (variable.value && variable.placeholder) {
          const placeholder = String(variable.placeholder)
          const value = String(variable.value)
          console.log(`Replacing ${value} with ${placeholder}`)
          // Replace the real value with the placeholder
          try {
            const valueRegex = new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')
            const beforeReplace = updatedContent
            updatedContent = updatedContent.replace(valueRegex, placeholder)
            if (beforeReplace !== updatedContent) {
              console.log(`✅ Successfully replaced ${value}`)
            } else {
              console.log(`❌ No match found for ${value}`)
            }
          } catch (error) {
            console.error(`Error replacing value ${value}:`, error)
          }
        }
      })
    }
    
    console.log('Toggle updated content:', updatedContent)
    setDocumentContent(updatedContent)
  }, [showRealValues, documentContent, variables])

  // Handle AI rewrite
  const handleAIRewrite = useCallback(async () => {
    if (!improvementPrompt.trim()) {
      setSnackbarMessage('Por favor, descreva a melhoria desejada')
      setSnackbarOpen(true)
      return
    }

    try {
      // Show loading state
      setSnackbarMessage('Reescrevendo com IA...')
      setSnackbarOpen(true)
      
      const result = await rewriteWithAIMutation.mutateAsync({
        id: minuta.id,
        data: {
          improvement_prompt: improvementPrompt,
          selected_text: selectedText || undefined
        }
      })

      // Update content with AI result
      setDocumentContent(result.corpo_md)
      setImprovementPrompt('')
      setSelectedText('')
      setSnackbarMessage('Documento reescrito com IA com sucesso!')
      setSnackbarOpen(true)
    } catch (error: any) {
      console.error('AI rewrite failed:', error)
      const errorMessage = error?.response?.data?.error || error?.message || 'Erro desconhecido'
      setSnackbarMessage(`Erro ao reescrever com IA: ${errorMessage}`)
      setSnackbarOpen(true)
    }
  }, [minuta.id, improvementPrompt, selectedText, rewriteWithAIMutation])

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }


  const handleClose = () => {
    if (hasUnsavedChanges) {
      if (window.confirm('Você tem alterações não salvas. Deseja realmente fechar?')) {
        onClose()
      }
    } else {
      onClose()
    }
  }

  return (
    <>
      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: {
            height: '95vh',
            maxHeight: '95vh'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          pb: 2
        }}>
          <Box>
            <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
              Documento Gerado
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {minuta.processo.tipo_ato} • Versão {minuta.versao} • ID: {minuta.id}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Auto-save status */}
            <Typography variant="body2" color="text.secondary">
              {isSaving && <CircularProgress size={16} sx={{ mr: 1 }} />}
              {!isSaving && lastSaved && (
                <Chip 
                  label={`Salvo às ${lastSaved.toLocaleTimeString('pt-BR')}`} 
                  size="small" 
                  color="success" 
                  variant="outlined"
                />
              )}
              {hasUnsavedChanges && !isSaving && (
                <Chip 
                  label="Alterações não salvas" 
                  size="small" 
                  color="warning" 
                  variant="outlined"
                />
              )}
            </Typography>
            
            <IconButton onClick={handleClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent sx={{ p: 0, overflow: 'hidden' }}>
          <Box sx={{ display: 'flex', height: '100%' }}>
            {/* Document Editor */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
              <Paper 
                elevation={1} 
                sx={{ 
                  p: 0,
                  minHeight: '100%',
                  backgroundColor: 'background.paper',
                  border: 1,
                  borderColor: 'divider'
                }}
              >
                <RichTextEditor
                  content={documentContent}
                  onChange={handleContentChange}
                  onSelectionChange={setSelectedText}
                  placeholder="Digite o conteúdo do documento..."
                  editable={isEditing}
                  className="w-full h-full"
                />
              </Paper>
            </Box>

            {/* Information Panel */}
            <Box sx={{ 
              width: 400, 
              borderLeft: 1, 
              borderColor: 'divider',
              p: 3,
              backgroundColor: 'grey.50',
              overflow: 'auto'
            }}>
              {/* Variables Section */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Variáveis
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showRealValues}
                        onChange={toggleVariableDisplayMode}
                        size="small"
                      />
                    }
                    label="Ver valores reais"
                    labelPlacement="start"
                  />
                </Box>
                
                <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                  {variables.map((variable) => (
                    <Box key={variable.name} sx={{ mb: 2 }}>
                      <VariableInput
                        variable={variable}
                        showRealValues={showRealValues}
                        onChange={handleVariableChange}
                      />
                      {validateVariableValue(variable.name, variable.value) && (
                        <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                          {validateVariableValue(variable.name, variable.value)}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* AI Improvement Section */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Melhorias com IA
                </Typography>
                <TextField
                  multiline
                  rows={3}
                  value={improvementPrompt}
                  onChange={(e) => setImprovementPrompt(e.target.value)}
                  placeholder="Peça melhorias ou edições para a IA..."
                  fullWidth
                  size="small"
                  margin="dense"
                  disabled={false}
                />
                
                {selectedText && (
                  <Alert severity="info" sx={{ mt: 1, mb: 1 }}>
                    <Typography variant="caption" display="block">
                      Texto selecionado:
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      &ldquo;{selectedText}&rdquo;
                    </Typography>
                  </Alert>
                )}
                
                <Button
                  variant="contained"
                  startIcon={<AIIcon />}
                  onClick={handleAIRewrite}
                  disabled={!improvementPrompt.trim() || rewriteWithAIMutation.isPending}
                  fullWidth
                  sx={{ mt: 1 }}
                  color="secondary"
                >
                  {rewriteWithAIMutation.isPending ? (
                    <>
                      <CircularProgress size={16} sx={{ mr: 1 }} />
                      Reescrevendo...
                    </>
                  ) : selectedText ? (
                    'Reescrever seleção com IA'
                  ) : (
                    'Reescrever com IA'
                  )}
                </Button>
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
            onClick={onShare}
          >
            Compartilhar
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<PrintIcon />}
            onClick={onPrint}
          >
            Imprimir
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={onDownloadPDF}
          >
            Baixar PDF
          </Button>
          
          <Button
            variant="contained"
            onClick={handleClose}
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

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarMessage.includes('Erro') ? "error" : "success"}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  )
}
