import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

const resourceKeys = (resource: string) => ({
  list: () => [resource, 'list'] as const,
  detail: (id: string) => [resource, 'detail', id] as const,
})

export const queryKeys = {
  auth: { currentUser: ['auth', 'currentUser'] as const },
  tenants: resourceKeys('tenants'),
  processos: resourceKeys('processos'),
  documentos: resourceKeys('documentos'),
  minutas: resourceKeys('minutas'),
  templates: resourceKeys('templates'),
  ai: { suggestClauses: () => ['ai', 'suggestClauses'] as const },
  assistente: {
    conversation: () => ['assistente', 'conversation'] as const,
    faq: () => ['assistente', 'faq'] as const,
    suggestions: () => ['assistente', 'suggestions'] as const,
  },
  workflow: {
    tasks: () => ['workflow', 'tasks'] as const,
    dashboard: () => ['workflow', 'dashboard'] as const,
  },
}
