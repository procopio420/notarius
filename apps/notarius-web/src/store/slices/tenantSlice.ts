import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Tenant {
  id: string
  nome: string
  cnpj: string
  uf: string
  cidade: string
  endereco: string
  telefone: string
  email: string
  is_active: boolean
}

interface TenantState {
  selectedTenant: Tenant | null
  availableTenants: Tenant[]
  isLoading: boolean
}

interface TenantActions {
  setSelectedTenant: (tenant: Tenant) => void
  setAvailableTenants: (tenants: Tenant[]) => void
  setLoading: (loading: boolean) => void
  clearTenants: () => void
}

export const useTenantStore = create<TenantState & TenantActions>()(
  persist(
    (set) => ({
      // State
      selectedTenant: null,
      availableTenants: [],
      isLoading: false,

      // Actions
      setSelectedTenant: (selectedTenant) => set({ selectedTenant }),
      setAvailableTenants: (availableTenants) => set({ availableTenants }),
      setLoading: (isLoading) => set({ isLoading }),
      clearTenants: () => set({ 
        selectedTenant: null, 
        availableTenants: [],
        isLoading: false 
      }),
    }),
    {
      name: 'tenant-storage',
      partialize: (state) => ({ 
        selectedTenant: state.selectedTenant 
      }),
    }
  )
)

