import axios from 'axios'

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
