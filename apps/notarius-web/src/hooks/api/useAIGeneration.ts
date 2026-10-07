import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
interface GenerateFromIntentRequest {
  intent: string
  processo_id: string
  user_id: string
}

interface GenerateFromIntentResponse {
  minuta: {
    id: string
    versao: number
    corpo_md: string
    variaveis_json: Record<string, string>
    status: string
    gerada_por: string
    citations: Array<{
      source: string
      article: string
      confidence: number
    }>
    grounding_confidence: number
  }
  parsed_intent: {
    action: string
    document_type: string
    entities: Record<string, any>
    confidence: number
  }
  legal_citations: Array<{
    source: string
    relevance: number
    excerpt: string
  }>
}

interface ApproveMinutaRequest {
  approved_by: string
  notes?: string
}

interface ApproveMinutaResponse {
  minuta: {
    id: string
    status: string
    approved_at: string
    approved_by: string
  }
}

// Generate minuta from natural language intent
export const useGenerateFromIntent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'generate-from-intent'],
    mutationFn: async (data: GenerateFromIntentRequest): Promise<GenerateFromIntentResponse> => {
      const response = await api.post(endpoints.generateMinuta, data)
      return response.data
    },
    onSuccess: () => {
      // Invalidate minutas list to show new item
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: any) => {
      console.error('AI generation failed:', error)
      throw error
    },
  })
}

// Approve minuta
export const useApproveMinuta = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'approve'],
    mutationFn: async ({ id, data }: { id: string; data: ApproveMinutaRequest }): Promise<ApproveMinutaResponse> => {
      const response = await api.post(endpoints.approveMinuta(id), data)
      return response.data
    },
    onSuccess: (result) => {
      // Update the specific minuta in cache
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.detail(result.minuta.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Approve minuta failed:', error)
    },
  })
}

// Finalize minuta (generate final PDF)
export const useFinalizeMinuta = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'finalize'],
    mutationFn: async (id: string): Promise<{ documento: { id: string; s3_key: string; url: string } }> => {
      const response = await api.post(endpoints.finalizeMinuta(id))
      return response.data
    },
    onSuccess: (_, minutaId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.detail(minutaId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Finalize minuta failed:', error)
    },
  })
}

