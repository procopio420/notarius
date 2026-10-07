import { useAuthStore } from './slices/authSlice'
import { useTenantStore } from './slices/tenantSlice'

// Re-export all stores for convenience
export { useAuthStore } from './slices/authSlice'
export { useTenantStore } from './slices/tenantSlice'

// Combined store hook for components that need both auth and tenant
export const useAppStore = () => {
  const auth = useAuthStore()
  const tenant = useTenantStore()
  
  return {
    auth,
    tenant,
  }
}

// Helper hook to get current tenant ID for API calls
export const useCurrentTenantId = () => {
  const selectedTenant = useTenantStore((state) => state.selectedTenant)
  return selectedTenant?.id || null
}

// Helper hook to check if user is authenticated and has a tenant selected
export const useIsReady = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const selectedTenant = useTenantStore((state) => state.selectedTenant)
  
  return isAuthenticated && selectedTenant !== null
}

