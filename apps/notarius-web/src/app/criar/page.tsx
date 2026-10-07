'use client'

import { useState } from 'react'
import { useAnalyzeCommand, useGenerateDocument } from '@/hooks/api/useAI'
import { PromptInput } from '@/components/criar/PromptInput'
import { AnalysisResult } from '@/components/criar/AnalysisResult'
import { EmptyState } from '@/components/criar/EmptyState'
import { LoadingState } from '@/components/criar/LoadingState'
import { ErrorState } from '@/components/criar/ErrorState'
import { EnhancedDocumentViewer } from '@/components/documentos/EnhancedDocumentViewer'
import { MainLayout } from '@/components/layout/main-layout'
import { Container, Paper, Box } from '@mui/material'

type AnalysisState = 'empty' | 'loading' | 'result' | 'error'

export default function CriarPage() {
  const [analysisState, setAnalysisState] = useState<AnalysisState>('empty')
  const [currentCommand, setCurrentCommand] = useState('')
  const [analysisResult, setAnalysisResult] = useState<{
    parsed_intent: {
      document_type: string
      parties: Array<{
        name: string
        role: string
        cpf?: string
        email?: string
      }>
      metadata: {
        validity_days?: number
        location?: string
        special_conditions?: string[]
      }
      confidence_score: number
    }
    suggested_clauses?: Array<{
      id: string
      nome: string
      texto: string
      categoria: string
    }>
  } | null>(null)
  const [error, setError] = useState('')
  const [generatedDocument, setGeneratedDocument] = useState<{
    minuta: {
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
    ai_generation: {
      id: string
      confidence_score: number
      generation_time_ms: number
    }
  } | null>(null)

  const analyzeMutation = useAnalyzeCommand()
  const generateMutation = useGenerateDocument()

  const handleAnalyze = async (command: string) => {
    setCurrentCommand(command)
    setAnalysisState('loading')
    setError('')

    try {
      const result = await analyzeMutation.mutateAsync({ command })
      setAnalysisResult(result)
      setAnalysisState('result')
    } catch (err: unknown) {
      console.error('Analysis error:', err)
      let errorMessage = 'Erro ao analisar o comando'
      
      if (err instanceof Error) {
        errorMessage = err.message
      } else if (typeof err === 'string') {
        errorMessage = err
      } else if (err && typeof err === 'object' && 'message' in err) {
        errorMessage = (err as { message: string }).message
      }
      
      setError(errorMessage)
      setAnalysisState('error')
    }
  }
console.log('generatedDocument', generatedDocument)
  const handleProceed = async () => {
    if (!analysisResult) return

    try {
      const result = await generateMutation.mutateAsync({
        original_command: currentCommand,
        parsed_intent: analysisResult.parsed_intent,
        selected_clauses: analysisResult.suggested_clauses?.map((c) => c.id) || [],
      })

      // Store the generated document and show the viewer
      setGeneratedDocument(result)
      console.log('Document and process created:', result)
      
    } catch (err: unknown) {
      console.error('Generation error:', err)
      let errorMessage = 'Erro ao criar o documento'
      
      if (err instanceof Error) {
        errorMessage = err.message
      } else if (typeof err === 'string') {
        errorMessage = err
      } else if (err && typeof err === 'object' && 'message' in err) {
        errorMessage = (err as { message: string }).message
      }
      
      setError(errorMessage)
      setAnalysisState('error')
    }
  }

  const handleEdit = () => {
    setAnalysisState('empty')
    setAnalysisResult(null)
  }

  const handleRetry = () => {
    if (currentCommand) {
      handleAnalyze(currentCommand)
    }
  }

  const renderRightPanel = () => {
    switch (analysisState) {
      case 'loading':
        return <LoadingState />
      case 'result':
        return (
          <AnalysisResult
            parsedIntent={analysisResult?.parsed_intent || {
              document_type: '',
              parties: [],
              metadata: {},
              confidence_score: 0,
            }}
            onProceed={handleProceed}
            onEdit={handleEdit}
            isGenerating={generateMutation.isPending}
          />
        )
      case 'error':
        return <ErrorState error={error} onRetry={handleRetry} />
      default:
        return <EmptyState />
    }
  }

  return (
    <MainLayout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 3, height: 'calc(100vh - 12rem)' }}>
          {/* Left Panel - Input */}
          <Box sx={{ flex: 1 }}>
            <Paper sx={{ p: 3, height: '100%', overflow: 'auto' }}>
              <PromptInput
                onSubmit={handleAnalyze}
                isLoading={analyzeMutation.isPending || generateMutation.isPending}
                defaultValue={currentCommand}
              />
            </Paper>
          </Box>

          {/* Right Panel - Results */}
          <Box sx={{ flex: 1 }}>
            <Paper sx={{ p: 3, height: '100%', overflow: 'auto' }}>
              {renderRightPanel()}
            </Paper>
          </Box>
        </Box>
      </Container>

      {/* Document Viewer Modal */}
      {generatedDocument && (
        <EnhancedDocumentViewer
          open={!!generatedDocument}
          onClose={() => setGeneratedDocument(null)}
          minuta={{
            id: generatedDocument.minuta.id,
            versao: generatedDocument.minuta.versao,
            corpo_md: generatedDocument.minuta.corpo_md,
            variaveis_json: generatedDocument.minuta.variaveis_json,
            status: 'rascunho',
            gerada_por: 'ai',
            processo: generatedDocument.processo,
            created_by: {
              id: '1',
              username: 'system',
              first_name: 'Sistema',
              last_name: 'IA'
            },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            grounding_confidence: generatedDocument.ai_generation.confidence_score
          }}
          onShare={() => {
            if (navigator.share) {
              navigator.share({
                title: `Documento - ${generatedDocument.processo.tipo_ato}`,
                text: `Documento gerado automaticamente pelo sistema Notarius`,
                url: window.location.href
              })
            } else {
              navigator.clipboard.writeText(window.location.href)
            }
          }}
          onPrint={() => window.print()}
          onDownloadPDF={async () => {
            try {
              const token = localStorage.getItem('auth_token')
              const tenantId = localStorage.getItem('tenant_id')
              if (!token || !tenantId) {
                alert('Please login to download documents')
                return
              }

              // First, approve the minuta
              const approveResponse = await fetch(
                `http://localhost:8000/api/v1/ai/approve-minuta/${generatedDocument.minuta.id}/`,
                {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`,
                    'X-Tenant-ID': tenantId || ''
                  }
                }
              )

              if (!approveResponse.ok) {
                const error = await approveResponse.json()
                throw new Error(error.detail || 'Approve failed')
              }

              // Then, finalize the minuta
              const response = await fetch(
                `http://localhost:8000/api/v1/ai/finalize-minuta/${generatedDocument.minuta.id}/`,
                {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`,
                    'X-Tenant-ID': tenantId || ''
                  }
                }
              )
              
              if (!response.ok) {
                const error = await response.json()
                throw new Error(error.detail || 'Download failed')
              }
              
              // Check response type
              const contentType = response.headers.get('content-type')
              if (contentType?.includes('application/pdf')) {
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `${generatedDocument.processo.tipo_ato}-${generatedDocument.minuta.id}.pdf`
                document.body.appendChild(a)
                a.click()
                window.URL.revokeObjectURL(url)
                document.body.removeChild(a)
              } else {
                const data = await response.json()
                if (data.documento?.url) {
                  window.open(data.documento.url, '_blank')
                }
              }
            } catch (error) {
              console.error('Download failed:', error)
              const errorMessage = error instanceof Error ? error.message : 'Unknown error'
              alert(`Download failed: ${errorMessage}`)
            }
          }}
        />
      )}
    </MainLayout>
  )
}
