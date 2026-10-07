import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
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

interface ProcessoListResponse {
  results: Processo[]
  count: number
  next?: string
  previous?: string
}

interface CreateProcessoRequest {
  tipo_ato: string
  observacoes?: string
}

interface UpdateProcessoRequest {
  tipo_ato?: string
  status?: string
  observacoes?: string
}

// Get processos list
export const useProcessos = (params?: {
  search?: string
  status?: string
  tipo_ato?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: [...queryKeys.processos.list(), params],
    queryFn: async (): Promise<ProcessoListResponse> => {
      const searchParams = new URLSearchParams()
      if (params?.search) searchParams.append('search', params.search)
      if (params?.status) searchParams.append('status', params.status)
      if (params?.tipo_ato) searchParams.append('tipo_ato', params.tipo_ato)
      if (params?.page) searchParams.append('page', params.page.toString())
      if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
      
      const response = await api.get(`/api/v1/processos/?${searchParams}`)
      return response.data
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Get single processo
export const useProcesso = (id: string) => {
  return useQuery({
    queryKey: queryKeys.processos.detail(id),
    queryFn: async (): Promise<Processo> => {
      const response = await api.get(`/api/v1/processos/${id}/`)
      return response.data
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Create processo mutation
export const useCreateProcesso = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['processos', 'create'],
    mutationFn: async (data: CreateProcessoRequest): Promise<Processo> => {
      const response = await api.post('/api/v1/processos/', data)
      return response.data
    },
    onSuccess: () => {
      // Invalidate and refetch processos list
      queryClient.invalidateQueries({ queryKey: queryKeys.processos.list() })
    },
    onError: (error: unknown) => {
      console.error('Create processo failed:', error)
    },
  })
}

// Update processo mutation
export const useUpdateProcesso = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['processos', 'update'],
    mutationFn: async ({ id, data }: { id: string; data: UpdateProcessoRequest }): Promise<Processo> => {
      const response = await api.patch(`/api/v1/processos/${id}/`, data)
      return response.data
    },
    onSuccess: (updatedProcesso) => {
      // Update the specific processo in cache
      queryClient.setQueryData(
        queryKeys.processos.detail(updatedProcesso.id),
        updatedProcesso
      )
      // Invalidate list to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.processos.list() })
    },
    onError: (error: unknown) => {
      console.error('Update processo failed:', error)
    },
  })
}

// Delete processo mutation
export const useDeleteProcesso = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['processos', 'delete'],
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/api/v1/processos/${id}/`)
    },
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.processos.detail(deletedId) })
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: queryKeys.processos.list() })
    },
    onError: (error: unknown) => {
      console.error('Delete processo failed:', error)
    },
  })
}
