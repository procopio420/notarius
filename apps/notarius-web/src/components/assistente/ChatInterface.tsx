'use client'

import { useState, useRef, useEffect } from 'react'
import { Button, TextField, Box, Typography, CircularProgress } from '@mui/material'
import { ChatMessage } from './ChatMessage'
import { useSendMessage, useRateResponse } from '@/hooks/api/useAssistente'
import { Send as PaperAirplaneIcon, Stop as StopIcon } from '@mui/icons-material'

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

interface ChatInterfaceProps {
  messages: ChatMessage[]
  onNewMessage?: (message: ChatMessage) => void
  context?: {
    processo_id?: string
    documento_id?: string
    minuta_id?: string
  }
}

export function ChatInterface({ messages, onNewMessage, context }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const sendMessageMutation = useSendMessage()
  const rateResponseMutation = useRateResponse()

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [inputValue])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    }

    // Add user message immediately
    onNewMessage?.(userMessage)
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await sendMessageMutation.mutateAsync({
        message: userMessage.content,
        context
      })

      // Add AI response
      onNewMessage?.(response.message)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date().toISOString()
      }
      onNewMessage?.(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleRateMessage = async (messageId: string, rating: 'thumbs_up' | 'thumbs_down') => {
    try {
      await rateResponseMutation.mutateAsync({ messageId, rating })
    } catch (error) {
      console.error('Failed to rate message:', error)
    }
  }

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages Area */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {messages.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Box sx={{ color: 'text.disabled', mb: 2 }}>
              <svg width={48} height={48} style={{ margin: '0 auto' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </Box>
            <Typography color="text.secondary">Inicie uma conversa com o assistente</Typography>
          </Box>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onRate={handleRateMessage}
              onCopy={handleCopyMessage}
            />
          ))
        )}
        
        {isLoading && (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ flexShrink: 0, width: 32, height: 32, borderRadius: '50%', bgcolor: 'grey.100', color: 'text.secondary', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width={16} height={16} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </Box>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'inline-block', p: 2, borderRadius: 1, bgcolor: 'white', border: 1, borderColor: 'grey.200' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">Assistente está digitando...</Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box sx={{ borderTop: 1, borderColor: 'grey.200', p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            inputRef={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua pergunta..."
            multiline
            maxRows={4}
            fullWidth
            disabled={isLoading}
            size="small"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            sx={{ px: 2 }}
          >
            {isLoading ? (
              <StopIcon sx={{ fontSize: 16 }} />
            ) : (
              <PaperAirplaneIcon sx={{ fontSize: 16 }} />
            )}
          </Button>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Pressione Enter para enviar, Shift+Enter para nova linha
          </Typography>
          {context && (
            <Typography variant="caption" color="text.secondary">
              Contexto: {context.processo_id ? 'Processo' : context.documento_id ? 'Documento' : 'Minuta'}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  )
}
