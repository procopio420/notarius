import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
interface DocumentTemplate {
  id: string
  tenant: string
  name: string
  document_type: 'procuracao' | 'certidao' | 'testamento' | 'escritura' | 'contrato'
  template_path: string
  is_default: boolean
  is_active: boolean
  version: string
  description: string
  created_by: string
  created_at: string
  updated_at: string
}

interface TemplateListResponse {
  results: DocumentTemplate[]
  count: number
  next?: string
  previous?: string
}

interface CreateTemplateRequest {
  name: string
  document_type: string
  template_path: string
  is_default?: boolean
  is_active?: boolean
  version?: string
  description?: string
}

interface UpdateTemplateRequest {
  name?: string
  template_path?: string
  is_default?: boolean
  is_active?: boolean
  version?: string
  description?: string
}

// Get templates list
export const useTemplates = (params?: {
  document_type?: string
  is_active?: boolean
  is_default?: boolean
  search?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: [...queryKeys.templates.list(), params],
    queryFn: async (): Promise<TemplateListResponse> => {
      const searchParams = new URLSearchParams()
      if (params?.document_type) searchParams.append('document_type', params.document_type)
      if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString())
      if (params?.is_default !== undefined) searchParams.append('is_default', params.is_default.toString())
      if (params?.search) searchParams.append('search', params.search)
      if (params?.page) searchParams.append('page', params.page.toString())
      if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
      
      const response = await api.get(`${endpoints.templates}?${searchParams}`)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Get single template
export const useTemplate = (id: string) => {
  return useQuery({
    queryKey: queryKeys.templates.detail(id),
    queryFn: async (): Promise<DocumentTemplate> => {
      const response = await api.get(`${endpoints.templates}${id}/`)
      return response.data
    },
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Get default template for document type
export const useDefaultTemplate = (documentType: string) => {
  return useQuery({
    queryKey: ['templates', 'default', documentType],
    queryFn: async (): Promise<DocumentTemplate> => {
      const response = await api.get(`${endpoints.templates}?document_type=${documentType}&is_default=true`)
      return response.data.results[0]
    },
    enabled: !!documentType,
    staleTime: 10 * 60 * 1000,
  })
}

// Create template mutation
export const useCreateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['templates', 'create'],
    mutationFn: async (data: CreateTemplateRequest): Promise<DocumentTemplate> => {
      const response = await api.post(endpoints.templates, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates.list() })
    },
    onError: (error: unknown) => {
      console.error('Create template failed:', error)
    },
  })
}

// Update template mutation
export const useUpdateTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['templates', 'update'],
    mutationFn: async ({ id, data }: { id: string; data: UpdateTemplateRequest }): Promise<DocumentTemplate> => {
      const response = await api.patch(`${endpoints.templates}${id}/`, data)
      return response.data
    },
    onSuccess: (updatedTemplate) => {
      queryClient.setQueryData(
        queryKeys.templates.detail(updatedTemplate.id),
        updatedTemplate
      )
      queryClient.invalidateQueries({ queryKey: queryKeys.templates.list() })
    },
    onError: (error: unknown) => {
      console.error('Update template failed:', error)
    },
  })
}

// Delete template mutation
export const useDeleteTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['templates', 'delete'],
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`${endpoints.templates}${id}/`)
    },
    onSuccess: (_, deletedId) => {
      queryClient.removeQueries({ queryKey: queryKeys.templates.detail(deletedId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.templates.list() })
    },
    onError: (error: unknown) => {
      console.error('Delete template failed:', error)
    },
  })
}

