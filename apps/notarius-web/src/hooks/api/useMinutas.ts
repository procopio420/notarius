import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
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

interface MinutaListResponse {
  results: Minuta[]
  count: number
  next?: string
  previous?: string
}

interface CreateMinutaRequest {
  processo_id: string
  template_id?: string
  corpo_md: string
  variaveis_json?: Record<string, unknown>
  origem?: string
}

interface UpdateMinutaRequest {
  corpo_md?: string
  variaveis_json?: Record<string, unknown>
}

interface UpdateContentRequest {
  corpo_md?: string
  variaveis_json?: Record<string, unknown>
}

interface RewriteWithAIRequest {
  improvement_prompt: string
  selected_text?: string
}

// Get minutas list
export const useMinutas = (params?: {
  search?: string
  processo_id?: string
  origem?: string
  created_by?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: [...queryKeys.minutas.list(), params],
    queryFn: async (): Promise<MinutaListResponse> => {
      const searchParams = new URLSearchParams()
      if (params?.search) searchParams.append('search', params.search)
      if (params?.processo_id) searchParams.append('processo_id', params.processo_id)
      if (params?.origem) searchParams.append('origem', params.origem)
      if (params?.created_by) searchParams.append('created_by', params.created_by)
      if (params?.page) searchParams.append('page', params.page.toString())
      if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
      
      const response = await api.get(`${endpoints.minutas}?${searchParams}`)
      return response.data
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Get single minuta
export const useMinuta = (id: string) => {
  return useQuery({
    queryKey: queryKeys.minutas.detail(id),
    queryFn: async (): Promise<Minuta> => {
      const response = await api.get(`${endpoints.minutas}${id}/`)
      return response.data
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Create minuta mutation
export const useCreateMinuta = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'create'],
    mutationFn: async (data: CreateMinutaRequest): Promise<Minuta> => {
      const response = await api.post(endpoints.minutas, data)
      return response.data
    },
    onSuccess: () => {
      // Invalidate and refetch minutas list
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Create minuta failed:', error)
    },
  })
}

// Update minuta mutation
export const useUpdateMinuta = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'update'],
    mutationFn: async ({ id, data }: { id: string; data: UpdateMinutaRequest }): Promise<Minuta> => {
      const response = await api.patch(`${endpoints.minutas}${id}/`, data)
      return response.data
    },
    onSuccess: (updatedMinuta) => {
      // Update the specific minuta in cache
      queryClient.setQueryData(
        queryKeys.minutas.detail(updatedMinuta.id),
        updatedMinuta
      )
      // Invalidate list to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Update minuta failed:', error)
    },
  })
}

// Delete minuta mutation
export const useDeleteMinuta = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'delete'],
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`${endpoints.minutas}${id}/`)
    },
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.minutas.detail(deletedId) })
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Delete minuta failed:', error)
    },
  })
}

// Generate PDF mutation
export const useGeneratePDF = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'generate_pdf'],
    mutationFn: async (id: string): Promise<{ pdf_url: string; generated_at: string }> => {
      const response = await api.post(endpoints.finalizeMinuta(id))
      return response.data
    },
    onSuccess: (data, minutaId) => {
      // Update the minuta in cache with PDF info
      queryClient.setQueryData(
        queryKeys.minutas.detail(minutaId),
        (oldData: Minuta | undefined) => {
          if (oldData) {
            return {
              ...oldData,
              pdf_url: data.pdf_url,
              pdf_generated_at: data.generated_at
            }
          }
          return oldData
        }
      )
      // Invalidate list to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Generate PDF failed:', error)
    },
  })
}

// Download PDF mutation
export const useDownloadPDF = () => {
  return useMutation({
    mutationKey: ['minutas', 'download_pdf'],
    mutationFn: async (id: string): Promise<Blob> => {
      const response = await api.post(endpoints.finalizeMinuta(id), {}, {
        responseType: 'blob',
      })
      return response.data
    },
    onError: (error: unknown) => {
      console.error('Download PDF failed:', error)
    },
  })
}

// Update content mutation (for auto-save)
export const useUpdateMinutaContent = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'update_content'],
    mutationFn: async ({ id, data }: { id: string; data: UpdateContentRequest }): Promise<Minuta> => {
      const response = await api.patch(`${endpoints.minutas}${id}/update_content/`, data)
      return response.data
    },
    onSuccess: (updatedMinuta) => {
      // Update the specific minuta in cache
      queryClient.setQueryData(
        queryKeys.minutas.detail(updatedMinuta.id),
        updatedMinuta
      )
      // Invalidate list to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Update minuta content failed:', error)
    },
  })
}

// Rewrite with AI mutation
export const useRewriteWithAI = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['minutas', 'rewrite_with_ai'],
    mutationFn: async ({ id, data }: { id: string; data: RewriteWithAIRequest }): Promise<Minuta> => {
      const response = await api.post(`${endpoints.minutas}${id}/rewrite_with_ai/`, data)
      return response.data
    },
    onSuccess: (updatedMinuta) => {
      // Update the specific minuta in cache
      queryClient.setQueryData(
        queryKeys.minutas.detail(updatedMinuta.id),
        updatedMinuta
      )
      // Invalidate list to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Rewrite with AI failed:', error)
    },
  })
}
