import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
interface Documento {
  id: string
  tipo: string
  nome_arquivo: string
  tamanho_bytes: number
  mime_type: string
  url_arquivo: string
  status_ocr: string
  data_upload: string
  data_atualizacao: string
  uploaded_by: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  processo?: {
    id: string
    tipo_ato: string
    numero_protocolo?: string
  }
  ocr_text?: string
  ocr_confidence?: number
}

interface DocumentoListResponse {
  results: Documento[]
  count: number
  next?: string
  previous?: string
}

interface UploadDocumentoRequest {
  arquivo: File
  tipo: string
  processo_id?: string
  observacoes?: string
}

interface UpdateDocumentoRequest {
  tipo?: string
  observacoes?: string
  processo_id?: string
}

// Get documentos list
export const useDocumentos = (params?: {
  search?: string
  tipo?: string
  status_ocr?: string
  processo_id?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: [...queryKeys.documentos.list(), params],
    queryFn: async (): Promise<DocumentoListResponse> => {
      const searchParams = new URLSearchParams()
      if (params?.search) searchParams.append('search', params.search)
      if (params?.tipo) searchParams.append('tipo', params.tipo)
      if (params?.status_ocr) searchParams.append('status_ocr', params.status_ocr)
      if (params?.processo_id) searchParams.append('processo_id', params.processo_id)
      if (params?.page) searchParams.append('page', params.page.toString())
      if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
      
      const response = await api.get(`/api/v1/documentos/?${searchParams}`)
      return response.data
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Get single documento
export const useDocumento = (id: string) => {
  return useQuery({
    queryKey: queryKeys.documentos.detail(id),
    queryFn: async (): Promise<Documento> => {
      const response = await api.get(`/api/v1/documentos/${id}/`)
      return response.data
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Upload documento mutation
export const useUploadDocumento = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['documentos', 'upload'],
    mutationFn: async (data: UploadDocumentoRequest): Promise<Documento> => {
      const formData = new FormData()
      formData.append('arquivo', data.arquivo)
      formData.append('tipo', data.tipo)
      if (data.processo_id) formData.append('processo_id', data.processo_id)
      if (data.observacoes) formData.append('observacoes', data.observacoes)

      const response = await api.post('/documentos/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: () => {
      // Invalidate and refetch documentos list
      queryClient.invalidateQueries({ queryKey: queryKeys.documentos.list() })
    },
    onError: (error: unknown) => {
      console.error('Upload documento failed:', error)
    },
  })
}

// Update documento mutation
export const useUpdateDocumento = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['documentos', 'update'],
    mutationFn: async ({ id, data }: { id: string; data: UpdateDocumentoRequest }): Promise<Documento> => {
      const response = await api.patch(`/api/v1/documentos/${id}/`, data)
      return response.data
    },
    onSuccess: (updatedDocumento) => {
      // Update the specific documento in cache
      queryClient.setQueryData(
        queryKeys.documentos.detail(updatedDocumento.id),
        updatedDocumento
      )
      // Invalidate list to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.documentos.list() })
    },
    onError: (error: unknown) => {
      console.error('Update documento failed:', error)
    },
  })
}

// Delete documento mutation
export const useDeleteDocumento = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['documentos', 'delete'],
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/api/v1/documentos/${id}/`)
    },
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.documentos.detail(deletedId) })
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: queryKeys.documentos.list() })
    },
    onError: (error: unknown) => {
      console.error('Delete documento failed:', error)
    },
  })
}

// Download documento mutation
export const useDownloadDocumento = () => {
  return useMutation({
    mutationKey: ['documentos', 'download'],
    mutationFn: async (id: string): Promise<Blob> => {
      const response = await api.get(`/api/v1/documentos/${id}/download/`, {
        responseType: 'blob',
      })
      return response.data
    },
    onError: (error: unknown) => {
      console.error('Download documento failed:', error)
    },
  })
}

// Get presigned URL for documento
export const usePresignedUrl = () => {
  return useMutation({
    mutationKey: ['documentos', 'presigned_url'],
    mutationFn: async (id: string): Promise<{ url: string; expires_in: number }> => {
      const response = await api.get(`/api/v1/documentos/${id}/presigned_url/`)
      return response.data
    },
    onError: (error: unknown) => {
      console.error('Get presigned URL failed:', error)
    },
  })
}
