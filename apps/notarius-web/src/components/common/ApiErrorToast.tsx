'use client'

import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ExclamationTriangleIcon, XCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'

export function ApiErrorToast() {
  const queryClient = useQueryClient()

  useEffect(() => {
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'observerAdded' || event.type === 'observerRemoved') {
        return
      }

      if (event.type === 'updated' && event.query.state.status === 'error') {
        const error = event.query.state.error as any
        
        // Don't show toast for 401/403 errors (handled by auth)
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          return
        }

        // Don't show toast for network errors (user might be offline)
        if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
          toast.error('Erro de conexão', {
            description: 'Verifique sua conexão com a internet e tente novamente.',
            icon: <XCircleIcon className="h-4 w-4" />,
            duration: 5000,
          })
          return
        }

        // Don't show toast for 404 errors (might be expected)
        if (error?.response?.status === 404) {
          return
        }

        // Show appropriate error message
        const status = error?.response?.status
        const message = error?.response?.data?.message || error?.message || 'Erro desconhecido'

        if (status >= 500) {
          toast.error('Erro do servidor', {
            description: 'Ocorreu um erro interno. Nossa equipe foi notificada.',
            icon: <ExclamationTriangleIcon className="h-4 w-4" />,
            duration: 8000,
          })
        } else if (status >= 400) {
          toast.error('Erro na requisição', {
            description: message,
            icon: <InformationCircleIcon className="h-4 w-4" />,
            duration: 5000,
          })
        } else {
          toast.error('Erro inesperado', {
            description: message,
            icon: <ExclamationTriangleIcon className="h-4 w-4" />,
            duration: 5000,
          })
        }
      }
    })

    return unsubscribe
  }, [queryClient])

  return null
}
