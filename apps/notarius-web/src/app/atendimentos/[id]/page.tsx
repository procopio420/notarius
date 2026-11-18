'use client'
import { useParams } from 'next/navigation'
import { ChatAtendimento } from '@/components/atendimentos/ChatAtendimento'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
export default function AtendimentoPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuthStore()
  const { selectedTenant } = useTenantStore()
  return <ChatAtendimento key={[id,user?.id,selectedTenant?.id].join(':')} id={id} />
}
