'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useUpdateMinutaContent, useRewriteWithAI } from '../../hooks/api/useMinutas'
import { useAutoSave } from '../../hooks/useAutoSave'
import { RichTextEditor } from '../editor/RichTextEditor'
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

interface GeneratedDocumentViewerProps {
  minuta: Minuta
  onClose: () => void
  onShare?: () => void
  onPrint?: () => void
  onDownloadPDF?: () => void
}

export function GeneratedDocumentViewer({
  minuta,
  onClose,
  onShare,
  onPrint,
  onDownloadPDF
}: GeneratedDocumentViewerProps) {
  // State
  const [documentContent, setDocumentContent] = useState(minuta.corpo_md)
  const [variables, setVariables] = useState<DocumentVariable[]>([])
  const [showRealValues, setShowRealValues] = useState(false)
  const [improvementPrompt, setImprovementPrompt] = useState('')
  const [selectedText, setSelectedText] = useState('')
  const [isEditing, setIsEditing] = useState(false)

  // Refs

  // API hooks
  const updateContentMutation = useUpdateMinutaContent()
  const rewriteWithAIMutation = useRewriteWithAI()

  // Initialize variables from document
  useEffect(() => {
    const extractedVars = extractVariablesFromDocument(minuta.corpo_md)
    const varsWithValues = updateVariableValues(extractedVars, minuta.variaveis_json)
    setVariables(varsWithValues)
  }, [minuta.corpo_md, minuta.variaveis_json])

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
      },
      enabled: isEditing
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
    
    const updatedContent = toggleVariableDisplay(
      documentContent,
      variables,
      newShowRealValues
    )
    setDocumentContent(updatedContent)
  }, [documentContent, variables, showRealValues])


  // Handle AI rewrite
  const handleAIRewrite = useCallback(async () => {
    if (!improvementPrompt.trim()) return

    try {
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
    } catch (error) {
      console.error('AI rewrite failed:', error)
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

  // Get confidence percentage
  const confidencePercentage = minuta.grounding_confidence 
    ? Math.round(minuta.grounding_confidence * 100)
    : 0

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Documento Gerado
            </h1>
            <p className="text-sm text-gray-600">
              {minuta.processo.tipo_ato} • Versão {minuta.versao}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Auto-save status */}
            <div className="text-sm text-gray-500">
              {isSaving && <span className="text-blue-600">Salvando...</span>}
              {!isSaving && lastSaved && (
                <span className="text-green-600">
                  Salvo às {lastSaved.toLocaleTimeString('pt-BR')}
                </span>
              )}
              {saveError && (
                <span className="text-red-600">
                  Erro ao salvar: {saveError.message}
                </span>
              )}
              {hasUnsavedChanges && !isSaving && (
                <span className="text-orange-600">Alterações não salvas</span>
              )}
            </div>
            
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Document Editor */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 p-6">
            <RichTextEditor
              content={documentContent}
              onChange={handleContentChange}
              onSelectionChange={setSelectedText}
              placeholder="Digite o conteúdo do documento..."
              editable={isEditing}
              className="w-full h-full"
            />
          </div>
          
          {/* Editor Controls */}
          <div className="border-t border-gray-200 bg-white px-6 py-3">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  isEditing
                    ? 'text-white bg-red-600 hover:bg-red-700 focus:ring-red-500'
                    : 'text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                }`}
              >
                {isEditing ? 'Parar Edição' : 'Editar Documento'}
              </button>
              
              <div className="text-sm text-gray-500">
                {isEditing ? 'Modo de edição ativo' : 'Clique em "Editar Documento" para começar'}
              </div>
            </div>
          </div>
        </div>

        {/* Information Panel */}
        <div className="w-96 border-l border-gray-200 bg-white overflow-auto">
          <div className="p-6 space-y-6">
            {/* Process Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Informações do Documento
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">ID:</span>
                  <span className="text-sm font-mono text-gray-900">
                    {minuta.id.slice(0, 8)}...
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Status:</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {minuta.status}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Generation Info */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Geração por IA
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Confiança:</span>
                  <span className="text-sm text-gray-900">{confidencePercentage}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Tempo:</span>
                  <span className="text-sm text-gray-900">0ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Origem:</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    IA Gerado
                  </span>
                </div>
              </div>
            </div>

            {/* Variables Section */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">
                  Variáveis
                </h4>
                <button
                  onClick={toggleVariableDisplayMode}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {showRealValues ? 'Ocultar valores reais' : 'Ver valores reais'}
                </button>
              </div>
              
              <div className="space-y-3">
                {variables.map((variable) => (
                  <div key={variable.name} className="space-y-1">
                    <label className="block text-xs font-medium text-gray-700">
                      {variable.name}
                    </label>
                    <input
                      type="text"
                      value={formatVariableValue(variable.name, variable.value)}
                      onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder={variable.placeholder}
                      disabled={!isEditing}
                    />
                    {validateVariableValue(variable.name, variable.value) && (
                      <p className="text-xs text-red-600">
                        {validateVariableValue(variable.name, variable.value)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* AI Improvement Section */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Melhorias com IA
              </h4>
              <div className="space-y-3">
                <textarea
                  value={improvementPrompt}
                  onChange={(e) => setImprovementPrompt(e.target.value)}
                  placeholder="Peça melhorias ou edições para a IA..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={!isEditing}
                />
                
                {selectedText && (
                  <div className="p-2 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-xs text-blue-800 font-medium mb-1">
                      Texto selecionado:
                    </p>
                    <p className="text-xs text-blue-700 italic">
                      &ldquo;{selectedText}&rdquo;
                    </p>
                  </div>
                )}
                
                <button
                  onClick={handleAIRewrite}
                  disabled={!improvementPrompt.trim() || rewriteWithAIMutation.isPending}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {rewriteWithAIMutation.isPending ? (
                    'Reescrevendo...'
                  ) : selectedText ? (
                    'Reescrever seleção com IA'
                  ) : (
                    'Reescrever com IA'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onShare}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
              </svg>
              Compartilhar
            </button>
            
            <button
              onClick={onPrint}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Imprimir
            </button>
            
            <button
              onClick={onDownloadPDF}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Baixar PDF
            </button>
          </div>
          
          <div className="text-sm text-gray-500">
            Última atualização: {formatDate(minuta.updated_at)}
          </div>
        </div>
      </div>
    </div>
  )
}

