import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'

// Types
interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: {
    confidence?: number
    sources?: string[]
    suggestions?: string[]
  }
}

interface SendMessageRequest {
  message: string
  context?: {
    processo_id?: string
    documento_id?: string
    minuta_id?: string
  }
}

interface SendMessageResponse {
  message: ChatMessage
  suggestions?: string[]
}

interface ConversationHistory {
  messages: ChatMessage[]
  total_messages: number
  last_activity: string
}

// Send message to AI assistant
export const useSendMessage = () => {
  return useMutation({
    mutationKey: ['assistente', 'send_message'],
    mutationFn: async (data: SendMessageRequest): Promise<SendMessageResponse> => {
      const response = await api.post('/assistente/send_message/', data)
      return response.data
    },
    onError: (error: unknown) => {
      console.error('Send message failed:', error)
    },
  })
}

// Get conversation history
export const useConversationHistory = (conversationId?: string) => {
  return useQuery({
    queryKey: [...queryKeys.assistente.conversation(), conversationId],
    queryFn: async (): Promise<ConversationHistory> => {
      const url = conversationId 
        ? `/assistente/conversation/${conversationId}/`
        : '/assistente/conversation/'
      const response = await api.get(url)
      return response.data
    },
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

// Get FAQ suggestions
export const useFAQSuggestions = () => {
  return useQuery({
    queryKey: queryKeys.assistente.faq(),
    queryFn: async (): Promise<string[]> => {
      const response = await api.get('/assistente/faq_suggestions/')
      return response.data.suggestions || []
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Get context-aware suggestions
export const useContextSuggestions = (context?: {
  processo_id?: string
  documento_id?: string
  minuta_id?: string
}) => {
  return useQuery({
    queryKey: [...queryKeys.assistente.suggestions(), context],
    queryFn: async (): Promise<string[]> => {
      const searchParams = new URLSearchParams()
      if (context?.processo_id) searchParams.append('processo_id', context.processo_id)
      if (context?.documento_id) searchParams.append('documento_id', context.documento_id)
      if (context?.minuta_id) searchParams.append('minuta_id', context.minuta_id)
      
      const response = await api.get(`/assistente/context_suggestions/?${searchParams}`)
      return response.data.suggestions || []
    },
    enabled: !!(context?.processo_id || context?.documento_id || context?.minuta_id),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Rate AI response
export const useRateResponse = () => {
  return useMutation({
    mutationKey: ['assistente', 'rate_response'],
    mutationFn: async ({ messageId, rating }: { messageId: string; rating: 'thumbs_up' | 'thumbs_down' }): Promise<void> => {
      await api.post('/assistente/rate_response/', {
        message_id: messageId,
        rating
      })
    },
    onError: (error: unknown) => {
      console.error('Rate response failed:', error)
    },
  })
}

// Clear conversation
export const useClearConversation = () => {
  return useMutation({
    mutationKey: ['assistente', 'clear_conversation'],
    mutationFn: async (): Promise<void> => {
      await api.post('/assistente/clear_conversation/')
    },
    onError: (error: unknown) => {
      console.error('Clear conversation failed:', error)
    },
  })
}
