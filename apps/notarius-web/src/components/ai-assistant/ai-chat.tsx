'use client'

import { useState, useRef, useEffect } from 'react'
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Box,
  TextField,
  Avatar,
  Paper,
  IconButton,
  CircularProgress,
} from '@mui/material'
import {
  AutoAwesome as SparklesIcon,
  Send as PaperAirplaneIcon,
  Description as DocumentTextIcon,
  CheckCircle as CheckCircleIcon,
  Warning as ExclamationTriangleIcon,
  Schedule as ClockIcon,
} from '@mui/icons-material'

interface Message {
  id: string
  type: 'user' | 'ai' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    confidence?: number
    documentType?: string
    generationTime?: number
    parsedIntent?: any
  }
}

interface AIChatProps {
  className?: string
  sx?: any
}

export function AIChat({ className, sx }: AIChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: 'Olá! Sou o assistente AI do Notarius. Posso ajudar você a criar documentos notariais usando linguagem natural. Tente algo como: "Fazer procuração pública de João Silva para Maria Oliveira, com poderes gerais."',
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Simulate AI response - in real app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `Entendi! Vou criar uma procuração pública com as seguintes informações:

**Documento:** Procuração Pública
**Outorgante:** João Silva
**Outorgado:** Maria Oliveira
**Poderes:** Gerais

Confiança: 95%
Tempo de processamento: 1.2s

O documento foi gerado com sucesso e está pronto para revisão. Deseja que eu crie também o fluxo de assinatura?`,
        timestamp: new Date(),
        metadata: {
          confidence: 0.95,
          documentType: 'procuracao',
          generationTime: 1200,
          parsedIntent: {
            document_type: 'procuracao',
            entities: {
              outorgante: 'João Silva',
              outorgado: 'Maria Oliveira',
              tipo_poderes: 'gerais'
            }
          }
        }
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: 'Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const getMessageIcon = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>U</Avatar>
      case 'ai':
        return <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}><SparklesIcon /></Avatar>
      case 'system':
        return <Avatar sx={{ width: 32, height: 32, bgcolor: 'grey.500' }}>S</Avatar>
    }
  }

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'default'
    if (confidence >= 0.9) return 'success'
    if (confidence >= 0.7) return 'warning'
    return 'error'
  }

  return (
    <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column', ...sx }}>
      <CardHeader sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SparklesIcon sx={{ fontSize: 24, color: 'primary.main' }} />
            AI Assistant
          </Typography>
          <Chip label="Online" color="success" size="small" />
        </Box>
      </CardHeader>
      
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
        {/* Messages */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                gap: 2,
                justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              {message.type !== 'user' && (
                <Box sx={{ flexShrink: 0 }}>
                  {getMessageIcon(message.type)}
                </Box>
              )}
              
              <Paper
                elevation={1}
                sx={{
                  maxWidth: '80%',
                  p: 2,
                  bgcolor: message.type === 'user'
                    ? 'primary.main'
                    : message.type === 'ai'
                    ? 'primary.50'
                    : 'grey.50',
                  color: message.type === 'user' ? 'white' : 'text.primary',
                  border: message.type === 'user' ? 'none' : 1,
                  borderColor: message.type === 'ai' ? 'primary.200' : 'grey.200'
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
                
                {message.metadata && (
                  <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {message.metadata.confidence && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                          label={`Confiança: ${Math.round(message.metadata.confidence * 100)}%`}
                          color={getConfidenceColor(message.metadata.confidence) as any}
                          size="small"
                        />
                        {message.metadata.generationTime && (
                          <Chip
                            icon={<ClockIcon />}
                            label={`${message.metadata.generationTime}ms`}
                            variant="outlined"
                            size="small"
                          />
                        )}
                      </Box>
                    )}
                    
                    {message.metadata.documentType && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DocumentTextIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                          Tipo: {message.metadata.documentType}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                )}
              </Paper>
              
              {message.type === 'user' && (
                <Box sx={{ flexShrink: 0 }}>
                  {getMessageIcon(message.type)}
                </Box>
              )}
            </Box>
          ))}
          
          {isLoading && (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Box sx={{ flexShrink: 0 }}>
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                  <SparklesIcon />
                </Avatar>
              </Box>
              <Paper elevation={1} sx={{ p: 2, bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="primary.main">
                    Processando...
                  </Typography>
                </Box>
              </Paper>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>
        
        {/* Input */}
        <Box sx={{ borderTop: 1, borderColor: 'divider', p: 2 }}>
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Digite seu comando em linguagem natural..."
              disabled={isLoading}
              size="small"
            />
            <IconButton
              type="submit"
              disabled={!input.trim() || isLoading}
              color="primary"
            >
              <PaperAirplaneIcon />
            </IconButton>
          </Box>
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Exemplos: "Fazer procuração pública de João Silva para Maria Oliveira, com poderes gerais"
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}
