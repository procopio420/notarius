'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/main-layout'
import { PageHeader } from '@/components/layout/PageHeader'
import { FAQButtons } from '@/components/assistente/FAQButtons'
import { ChatInterface } from '@/components/assistente/ChatInterface'
import { Button, Box, Paper, Typography, Avatar } from '@mui/material'
import { useFAQSuggestions, useClearConversation } from '@/hooks/api/useAssistente'
import { Delete as TrashIcon, SmartToy as CpuChipIcon } from '@mui/icons-material'

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

export default function AssistentePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [showFAQ, setShowFAQ] = useState(true)

  const { data: faqSuggestions } = useFAQSuggestions()
  const clearConversationMutation = useClearConversation()

  const handleQuestionClick = (question: string) => {
    // Add the question as a user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setShowFAQ(false)
  }

  const handleNewMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message])
  }

  const handleClearConversation = async () => {
    if (confirm('Tem certeza que deseja limpar a conversa?')) {
      try {
        await clearConversationMutation.mutateAsync()
        setMessages([])
        setShowFAQ(true)
      } catch (error) {
        console.error('Failed to clear conversation:', error)
      }
    }
  }

  return (
    <MainLayout>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Page Header */}
        <PageHeader
          title="Assistente IA"
          description="Obtenha ajuda e esclarecimentos sobre processos notariais"
        >
          <Button
            variant="outlined"
            onClick={handleClearConversation}
            startIcon={<TrashIcon />}
            disabled={clearConversationMutation.isPending}
          >
            Limpar Conversa
          </Button>
        </PageHeader>

        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', lg: '1fr 2fr' }, 
          gap: 3, 
          height: 'calc(100vh - 200px)' 
        }}>
          {/* FAQ Section */}
          <Box>
            <Paper sx={{ p: 3, height: '100%', overflow: 'auto' }}>
              {showFAQ && (
                <FAQButtons onQuestionClick={handleQuestionClick} />
              )}
              
              {!showFAQ && (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CpuChipIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" sx={{ fontWeight: 500, mb: 1 }}>
                    Conversa Ativa
                  </Typography>
                  <Typography color="text.secondary" sx={{ mb: 2 }}>
                    Use o chat ao lado para continuar a conversa
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => setShowFAQ(true)}
                  >
                    Ver Perguntas Frequentes
                  </Button>
                </Box>
              )}
            </Paper>
          </Box>

          {/* Chat Section */}
          <Box>
            <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider', p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.100', color: 'primary.main' }}>
                    <CpuChipIcon sx={{ fontSize: 16 }} />
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                      Assistente Notarius
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {messages.length > 0 ? `${messages.length} mensagens` : 'Pronto para ajudar'}
                    </Typography>
                  </Box>
                </Box>
              </Box>
              
              <ChatInterface
                messages={messages}
                onNewMessage={handleNewMessage}
              />
            </Paper>
          </Box>
        </Box>
      </Box>
    </MainLayout>
  )
}
