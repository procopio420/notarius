'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button } from '@mui/material'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore, type Tenant } from '@/store/slices/tenantSlice'

// Keep the existing server-side data boundary automatic, without a chooser.
export function EspacoAutomatico() {
  const { user, isAuthenticated } = useAuthStore()
  const { selectedTenant, setSelectedTenant } = useTenantStore()
  const query = useQuery({
    queryKey: [...queryKeys.tenants.list(), user?.id],
    enabled: isAuthenticated && !!user,
    queryFn: async (): Promise<Tenant[]> => {
      const response = await api.get('/auth/tenants/')
      return (response.data.tenants || []).map((item: Partial<Tenant>) => ({
        cnpj: '', cidade: '', endereco: '', telefone: '', email: '', is_active: true, ...item,
      }))
    },
  })
  useEffect(() => {
    if (!query.data?.length) return
    const preferred = user?.default_tenant?.id || window.localStorage.getItem('tenant_id')
    const target = query.data.find(item => item.id === preferred) || query.data[0]
    if (selectedTenant?.id !== target.id) setSelectedTenant(target)
  }, [query.data, user, selectedTenant, setSelectedTenant])
  if (query.isError) return <Alert severity="error" action={<Button onClick={() => query.refetch()}>Tentar novamente</Button>}>Não foi possível abrir seu espaço de trabalho.</Alert>
  if (query.isSuccess && !query.data.length) return <Alert severity="error">Sua conta ainda não tem um espaço de trabalho disponível.</Alert>
  return null
}
