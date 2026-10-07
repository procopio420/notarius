'use client'

import { CpuChipIcon } from '@heroicons/react/24/outline'

interface PageLoaderProps {
  message?: string
}

export function PageLoader({ message = 'Carregando...' }: PageLoaderProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
          <CpuChipIcon className="h-8 w-8 text-blue-600 animate-pulse" />
        </div>
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          {message}
        </h2>
        <div className="flex items-center justify-center space-x-1">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  )
}
