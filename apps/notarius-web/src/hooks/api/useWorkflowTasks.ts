import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
interface WorkflowTask {
  id: string
  titulo: string
  descricao: string
  tipo: string
  prioridade: string
  status: string
  assigned_to?: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  created_by: {
    id: string
    username: string
    first_name: string
    last_name: string
  }
  deadline?: string
  completed_at?: string
  created_at: string
  updated_at: string
  documento?: {
    id: string
    tipo: string
  }
  minuta?: {
    id: string
    versao: number
  }
  processo?: {
    id: string
    tipo_ato: string
  }
}

interface DashboardSummary {
  total_open_tasks: number
  total_pending: number
  total_in_progress: number
  total_overdue: number
  tasks_by_type: Array<{
    tipo: string
    count: number
  }>
  tasks_by_priority: Array<{
    prioridade: string
    count: number
  }>
}

// Get workflow tasks
export const useWorkflowTasks = (params?: {
  status?: string
  tipo?: string
  prioridade?: string
  assigned_to?: string
  limit?: number
}) => {
  return useQuery({
    queryKey: [...queryKeys.workflow.tasks(), params],
    queryFn: async (): Promise<WorkflowTask[]> => {
      const searchParams = new URLSearchParams()
      if (params?.status) searchParams.append('status', params.status)
      if (params?.tipo) searchParams.append('tipo', params.tipo)
      if (params?.prioridade) searchParams.append('prioridade', params.prioridade)
      if (params?.assigned_to) searchParams.append('assigned_to', params.assigned_to)
      if (params?.limit) searchParams.append('limit', params.limit.toString())
      
      // TODO: Enable when workflow endpoints are implemented
      // const response = await api.get(`/api/v1/workflow-tasks/?${searchParams}`)
      // return response.data.results || response.data
      
      // Return empty array until workflow endpoints are implemented
      return []
    },
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

// Get dashboard summary
export const useDashboardSummary = (assignedToUserId?: string) => {
  return useQuery({
    queryKey: [...queryKeys.workflow.dashboard(), assignedToUserId],
    queryFn: async (): Promise<DashboardSummary> => {
      const searchParams = new URLSearchParams()
      if (assignedToUserId) searchParams.append('assigned_to_user_id', assignedToUserId)
      
      // TODO: Enable when workflow endpoints are implemented
      // const response = await api.get(`/api/v1/workflow-tasks/dashboard/?${searchParams}`)
      // return response.data
      
      // Return empty dashboard until workflow endpoints are implemented
      return {
        total_tasks: 0,
        pending_tasks: 0,
        completed_tasks: 0,
        overdue_tasks: 0,
        tasks_by_status: {},
        tasks_by_priority: {},
        recent_tasks: []
      }
    },
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

// Get pending authentications queue
export const usePendingAuthentications = (limit = 10) => {
  return useQuery({
    queryKey: [...queryKeys.workflow.tasks(), 'authentication_queue', limit],
    queryFn: async (): Promise<WorkflowTask[]> => {
      // TODO: Enable when workflow endpoints are implemented
      // const response = await api.get(`/api/v1/workflow-tasks/authentication_queue/?limit=${limit}`)
      // return response.data
      
      // Return empty array until workflow endpoints are implemented
      return []
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}

// Get pending signatures queue
export const usePendingSignatures = (limit = 10) => {
  return useQuery({
    queryKey: [...queryKeys.workflow.tasks(), 'signature_queue', limit],
    queryFn: async (): Promise<WorkflowTask[]> => {
      // TODO: Enable when workflow endpoints are implemented
      // const response = await api.get(`/api/v1/workflow-tasks/signature_queue/?limit=${limit}`)
      // return response.data
      
      // Return empty array until workflow endpoints are implemented
      return []
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}

// Get pending reviews queue
export const usePendingReviews = (limit = 10) => {
  return useQuery({
    queryKey: [...queryKeys.workflow.tasks(), 'review_queue', limit],
    queryFn: async (): Promise<WorkflowTask[]> => {
      // TODO: Enable when workflow endpoints are implemented
      // const response = await api.get(`/api/v1/workflow-tasks/review_queue/?limit=${limit}`)
      // return response.data
      
      // Return empty array until workflow endpoints are implemented
      return []
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}
