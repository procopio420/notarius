import axios from 'axios'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
import { queryClient } from './queryClient'

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api/v1',
})

api.interceptors.request.use((config) => {
  // Callers may use either a resource path or the full API prefix.
  config.url = config.url?.replace(/^\/api\/v1\//, '/')
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token')
    const tenant = localStorage.getItem('tenant_id')
    if (token) config.headers.Authorization = `Token ${token}`
    if (tenant) config.headers['X-Tenant-ID'] = tenant
  }
  return config
})

api.interceptors.response.use(response => response, error => {
  const status = error.response?.status
  const invalidToken = status === 403 && error.response?.data?.detail === 'Invalid token.'
  if (typeof window !== 'undefined' && (status === 401 || invalidToken) && !error.config?.url?.includes('/auth/login/')) {
    const currentToken = localStorage.getItem('auth_token')
    // A late failure of the previous account must not end a newer login.
    if (!currentToken || error.config?.headers?.Authorization === `Token ${currentToken}`) {
      useAuthStore.getState().logout()
      useTenantStore.getState().clearTenants()
      localStorage.removeItem('auth_token')
      localStorage.removeItem('tenant_id')
      queryClient.clear()
    }
  }
  return Promise.reject(error)
})

export const endpoints = {
  login: '/auth/login/',
  logout: '/auth/logout/',
  userProfile: '/auth/me/',
  userTenants: '/auth/tenants/',
  setDefaultTenant: '/auth/set-default-tenant/',
  templates: '/templates/',
  minutas: '/minutas/',
  generateMinuta: '/ai/generate-minuta/',
  approveMinuta: (id: string) => `/ai/approve-minuta/${id}/`,
  finalizeMinuta: (id: string) => `/ai/finalize-minuta/${id}/`,
}
