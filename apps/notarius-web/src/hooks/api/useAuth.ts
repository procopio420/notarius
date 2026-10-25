import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { useAuthStore } from '@/store/slices/authSlice'
import { queryKeys } from '@/lib/queryClient'
import { useTenantStore } from '@/store/slices/tenantSlice'

// Types
interface LoginRequest {
  username: string
  password: string
}

interface Tenant {
  id: string
  nome: string
  uf: string
}

interface LoginResponse {
  token: string
  user: {
    id: string
    username: string
    email: string
    first_name: string
    last_name: string
    is_staff: boolean
    is_superuser: boolean
    tenants: Tenant[]
    default_tenant: Tenant | null
  }
  default_tenant: string | null  // Backend returns this as UUID string
}

interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
  is_superuser: boolean
  tenants: Tenant[]
  default_tenant: Tenant | null
}

// Login mutation
export const useLogin = () => {
  const queryClient = useQueryClient()
  const { login, setLoading } = useAuthStore()

  return useMutation({
    mutationKey: ['login'],
    mutationFn: async (credentials: LoginRequest): Promise<LoginResponse> => {
      setLoading(true)
      const response = await api.post(endpoints.login, credentials)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.clear()
      useTenantStore.getState().clearTenants()
      window.localStorage.removeItem('tenant_id')
      window.localStorage.setItem('auth_token', data.token)
      
      // Set default tenant in localStorage if available
      // Backend returns default_tenant as UUID string
      if (data.default_tenant) {
        window.localStorage.setItem('tenant_id', data.default_tenant)
      } else if (data.user.default_tenant && data.user.default_tenant.id) {
        window.localStorage.setItem('tenant_id', data.user.default_tenant.id)
      }
      login(data.user, data.token)
      
      // Invalidate and refetch user-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.currentUser })
    },
    onError: () => {
      console.error('Não foi possível entrar.')
    },
    onSettled: () => {
      setLoading(false)
    },
  })
}

// Logout mutation
export const useLogout = () => {
  const queryClient = useQueryClient()
  const { logout } = useAuthStore()

  return useMutation({
    mutationKey: ['logout'],
    mutationFn: async (): Promise<void> => {
      // Call logout endpoint if it exists
      try {
        await api.post(endpoints.logout)
      } catch {
        // Even if the API call fails, we should still logout locally
        console.warn('Não foi possível encerrar a sessão no servidor.')
      }
    },
    onSuccess: () => {
      logout()
      useTenantStore.getState().clearTenants()
      window.localStorage.removeItem('auth_token')
      window.localStorage.removeItem('tenant_id')
      // Clear all cached data
      queryClient.clear()
    },
    onError: () => {
      console.error('Não foi possível encerrar a sessão.')
      // Still logout locally even if API call fails
      logout()
      useTenantStore.getState().clearTenants()
      window.localStorage.removeItem('auth_token')
      window.localStorage.removeItem('tenant_id')
      queryClient.clear()
    },
  })
}

// Current user query
export const useCurrentUser = () => {
  const { token, isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: queryKeys.auth.currentUser,
    queryFn: async (): Promise<User> => {
      const response = await api.get(endpoints.userProfile)
      return response.data.user
    },
    enabled: isAuthenticated && !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Check if user is authenticated
export const useIsAuthenticated = () => {
  const { isAuthenticated, token } = useAuthStore()
  return isAuthenticated && !!token
}

// Get user's accessible tenants
export const useUserTenants = () => {
  const { isAuthenticated, token } = useAuthStore()

  return useQuery({
    queryKey: ['user-tenants'],
    queryFn: async (): Promise<{ tenants: Tenant[] }> => {
      const response = await api.get(endpoints.userTenants)
      return response.data
    },
    enabled: isAuthenticated && !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Set default tenant mutation
export const useSetDefaultTenant = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['set-default-tenant'],
    mutationFn: async (tenantId: string): Promise<{ detail: string; default_tenant: Tenant }> => {
      const response = await api.post(endpoints.setDefaultTenant, { tenant_id: tenantId })
      return response.data
    },
    onSuccess: (data) => {
      // Update localStorage with new default tenant
      window.localStorage.setItem('tenant_id', data.default_tenant.id)
      
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({ queryKey: ['user-tenants'] })
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.currentUser })
    },
    onError: () => {
      console.error('Não foi possível selecionar o cartório.')
    },
  })
}

