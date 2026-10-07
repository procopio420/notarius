/**
 * Generate Minuta Page - Generate legal documents from natural language
 */

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Minuta } from '../../../types/editor';

export default function GenerateMinutaPage() {
  const router = useRouter();
  const [command, setCommand] = useState('');
  const [processoId, setProcessoId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!command.trim()) {
      setError('Comando é obrigatório');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/minutas/generate-from-intent/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: command.trim(),
          processo_id: processoId || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro ao gerar minuta');
      }

      const data = await response.json();
      setResult(data);

      // Redirect to editor
      if (data.minuta_id) {
        router.push(`/minutas/${data.minuta_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao gerar minuta');
    } finally {
      setLoading(false);
    }
  };

  const exampleCommands = [
    "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP",
    "Criar escritura de compra e venda entre Maria Santos e Pedro Oliveira, imóvel na Rua das Flores, 123",
    "Fazer reconhecimento de firma para Ana Costa, CPF 987.654.321-00",
    "Criar testamento para Carlos Mendes, deixando todos os bens para sua filha",
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Gerar Minuta com IA
            </h1>
            <p className="text-gray-600">
              Descreva o documento que você precisa em linguagem natural e nossa IA irá gerar uma minuta legal completa.
            </p>
          </div>

          <form onSubmit={handleGenerate} className="space-y-6">
            <div>
              <label htmlFor="command" className="block text-sm font-medium text-gray-700 mb-2">
                Comando em Linguagem Natural *
              </label>
              <textarea
                id="command"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Ex: Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Seja específico sobre as partes envolvidas, tipo de documento e poderes/objetivos.
              </p>
            </div>

            <div>
              <label htmlFor="processoId" className="block text-sm font-medium text-gray-700 mb-2">
                ID do Processo (opcional)
              </label>
              <input
                type="text"
                id="processoId"
                value={processoId}
                onChange={(e) => setProcessoId(e.target.value)}
                placeholder="Deixe em branco para criar um novo processo"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Erro ao gerar minuta
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      {error}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading || !command.trim()}
                className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Gerando...' : 'Gerar Minuta'}
              </button>
            </div>
          </form>

          {/* Example Commands */}
          <div className="mt-12">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Exemplos de Comandos
            </h3>
            <div className="grid gap-3">
              {exampleCommands.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setCommand(example)}
                  className="text-left p-3 bg-gray-50 border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
                >
                  <span className="text-sm text-gray-700">{example}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Result Preview */}
          {result && (
            <div className="mt-8 bg-green-50 border border-green-200 rounded-md p-6">
              <h3 className="text-lg font-medium text-green-800 mb-4">
                Minuta Gerada com Sucesso!
              </h3>
              <div className="space-y-2 text-sm text-green-700">
                <p><strong>ID da Minuta:</strong> {result.minuta_id}</p>
                <p><strong>Confiança:</strong> {Math.round(result.confidence * 100)}%</p>
                <p><strong>Citações:</strong> {result.citations_count}</p>
                <p><strong>Status:</strong> {result.status}</p>
              </div>
              <div className="mt-4">
                <h4 className="font-medium text-green-800 mb-2">Preview:</h4>
                <div className="bg-white border border-green-200 rounded p-3 text-sm text-gray-700 max-h-32 overflow-y-auto">
                  {result.preview}
                </div>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => router.push(`/minutas/${result.minuta_id}`)}
                  className="px-4 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  Abrir no Editor
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
