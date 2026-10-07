/**
 * Minuta Editor Page - Main page for editing legal documents
 */

'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function MinutaEditorPage() {
  const params = useParams();
  const router = useRouter();
  const minutaId = params.id as string;

  const [isEditing, setIsEditing] = useState(false);
  const [documentContent, setDocumentContent] = useState(`# PROCURAÇÃO

Eu, **{{NOME_DO_OUTORGANTE}}**, brasileiro, solteiro, portador do RG nº **{{PLACEHOLDER_RG}}** e CPF nº **{{PLACEHOLDER_CPF}}**, residente e domiciliado à **{{PLACEHOLDER_ENDEREÇO}}**, venho por meio desta, outorgar poderes a **{{NOME_DO_OUTORGADO}}**.

## CLÁUSULA PRIMEIRA - DO OBJETO

O presente instrumento tem por objeto **{{OBJETO}}**.

## CLÁUSULA SEGUNDA - DOS PODERES

O outorgado fica autorizado a praticar todos os atos necessários para o cumprimento do objeto desta procuração.

## CLÁUSULA TERCEIRA - DA VALIDADE

Esta procuração terá validade de 1 (um) ano, contado da data de sua assinatura.

E por estar assim justo e contratado, firmo a presente procuração.

**{{CIDADE}}**, {{DATA}}.

_____________________________
**{{NOME_DO_OUTORGANTE}}**
CPF: {{PLACEHOLDER_CPF}}`);

  const [variables, setVariables] = useState({
    NOME_DO_OUTORGANTE: 'João Silva',
    NOME_DO_OUTORGADO: 'Maria Santos',
    PLACEHOLDER_RG: '12.345.678-9',
    PLACEHOLDER_CPF: '123.456.789-01',
    PLACEHOLDER_ENDEREÇO: 'Rua das Flores, 123, São Paulo/SP',
    OBJETO: 'representar em processos judiciais',
    CIDADE: 'São Paulo',
    DATA: '15 de dezembro de 2024'
  });

  const [showRealValues, setShowRealValues] = useState(false);
  const [improvementPrompt, setImprovementPrompt] = useState('');

  const handleClose = () => {
    router.back();
  };

  const handleShare = () => {
    console.log('Share document');
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = () => {
    console.log('Download PDF');
  };

  const handleContentChange = (newContent: string) => {
    setDocumentContent(newContent);
  };

  const handleVariableChange = (variableName: string, newValue: string) => {
    setVariables(prev => ({
      ...prev,
      [variableName]: newValue
    }));
    
    // Update document content
    const updatedContent = documentContent.replace(
      new RegExp(`{{${variableName}}}`, 'g'),
      newValue
    );
    setDocumentContent(updatedContent);
  };

  const toggleVariableDisplay = () => {
    setShowRealValues(!showRealValues);
  };

  const handleAIRewrite = () => {
    if (!improvementPrompt.trim()) return;
    
    // Simulate AI rewrite
    const rewrittenContent = documentContent + `\n\n[Melhoria aplicada: ${improvementPrompt}]`;
    setDocumentContent(rewrittenContent);
    setImprovementPrompt('');
  };

  const formatDate = (dateString: string) => {
    return new Date().toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

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
              procuracao • Versão 1
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={handleClose}
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
            <div
              contentEditable={isEditing}
              className="w-full h-full p-4 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent overflow-auto prose max-w-none"
              onInput={(e) => {
                const newContent = e.currentTarget.textContent || '';
                handleContentChange(newContent);
              }}
              suppressContentEditableWarning={true}
              style={{ minHeight: '400px' }}
              dangerouslySetInnerHTML={{
                __html: documentContent
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mb-4">$1</h1>')
                  .replace(/^## (.*$)/gm, '<h2 class="text-lg font-semibold mb-2 mt-4">$1</h2>')
                  .replace(/\n/g, '<br/>')
              }}
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
                    {minutaId.slice(0, 8)}...
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Status:</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    rascunho
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
                  <span className="text-sm text-gray-900">95%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Tempo:</span>
                  <span className="text-sm text-gray-900">1.2s</span>
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
                  onClick={toggleVariableDisplay}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {showRealValues ? 'Ocultar valores reais' : 'Ver valores reais'}
                </button>
              </div>
              
              <div className="space-y-3">
                {Object.entries(variables).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <label className="block text-xs font-medium text-gray-700">
                      {key}
                    </label>
                    <input
                      type="text"
                      value={showRealValues ? value : `{{${key}}}`}
                      onChange={(e) => handleVariableChange(key, e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder={`{{${key}}}`}
                      disabled={!isEditing}
                    />
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
                  placeholder="Peça melhorias ou edições para a IA..."
                  value={improvementPrompt}
                  onChange={(e) => setImprovementPrompt(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={!isEditing}
                />
                
                <button
                  onClick={handleAIRewrite}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={!isEditing || !improvementPrompt.trim()}
                >
                  Reescrever com IA
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
              onClick={handleShare}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
              </svg>
              Compartilhar
            </button>
            
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Imprimir
            </button>
            
            <button
              onClick={handleDownloadPDF}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Baixar PDF
            </button>
          </div>
          
          <div className="text-sm text-gray-500">
            Última atualização: {formatDate(new Date().toISOString())}
          </div>
        </div>
      </div>
    </div>
  );
}