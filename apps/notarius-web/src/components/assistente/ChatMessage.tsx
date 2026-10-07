'use client'

import { useState } from 'react'
import { Button, Box, Typography, Chip, Avatar, IconButton } from '@mui/material'
import { 
  Person as UserIcon, 
  SmartToy as CpuChipIcon, 
  ThumbUp as HandThumbUpIcon, 
  ThumbDown as HandThumbDownIcon,
  ContentCopy as ClipboardDocumentIcon
} from '@mui/icons-material'

interface ChatMessageProps {
  message: {
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
  onRate?: (messageId: string, rating: 'thumbs_up' | 'thumbs_down') => void
  onCopy?: (content: string) => void
}

export function ChatMessage({ message, onRate, onCopy }: ChatMessageProps) {
  const [showRating, setShowRating] = useState(false)

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatContent = (content: string) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
  }

  const isUser = message.role === 'user'

  return (
    <Box sx={{ display: 'flex', gap: 2, flexDirection: isUser ? 'row-reverse' : 'row' }}>
      {/* Avatar */}
      <Avatar sx={{ 
        width: 32, 
        height: 32, 
        bgcolor: isUser ? 'primary.main' : 'grey.100',
        color: isUser ? 'white' : 'text.secondary',
        flexShrink: 0
      }}>
        {isUser ? (
          <UserIcon sx={{ fontSize: 16 }} />
        ) : (
          <CpuChipIcon sx={{ fontSize: 16 }} />
        )}
      </Avatar>

      {/* Message Content */}
      <Box sx={{ 
        flex: 1, 
        maxWidth: '80%', 
        textAlign: isUser ? 'right' : 'left' 
      }}>
        <Box sx={{
          display: 'inline-block',
          p: 2,
          borderRadius: 2,
          bgcolor: isUser ? 'primary.main' : 'white',
          color: isUser ? 'white' : 'text.primary',
          border: isUser ? 'none' : 1,
          borderColor: 'grey.200'
        }}>
          <Box 
            sx={{ 
              '& strong': { fontWeight: 600 },
              '& em': { fontStyle: 'italic' }
            }}
            dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
          />
          
          {/* AI Message Metadata */}
          {!isUser && message.metadata && (
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'grey.200' }}>
              {message.metadata.confidence && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">Confiança:</Typography>
                  <Chip 
                    label={`${Math.round(message.metadata.confidence * 100)}%`}
                    color={message.metadata.confidence > 0.8 ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              )}
              
              {message.metadata.sources && message.metadata.sources.length > 0 && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">Fontes:</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {message.metadata.sources.map((source, index) => (
                      <Chip key={index} label={source} variant="outlined" size="small" />
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          )}
        </Box>

        {/* Message Footer */}
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1, 
          mt: 0.5,
          justifyContent: isUser ? 'flex-end' : 'flex-start'
        }}>
          <Typography variant="caption" color="text.secondary">
            {formatTime(message.timestamp)}
          </Typography>
          
          {!isUser && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <IconButton
                size="small"
                onClick={() => onCopy?.(message.content)}
                sx={{ 
                  width: 24, 
                  height: 24, 
                  color: 'text.disabled',
                  '&:hover': { color: 'text.primary' }
                }}
              >
                <ClipboardDocumentIcon sx={{ fontSize: 12 }} />
              </IconButton>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <IconButton
                  size="small"
                  onClick={() => {
                    onRate?.(message.id, 'thumbs_up')
                    setShowRating(true)
                  }}
                  sx={{ 
                    width: 24, 
                    height: 24, 
                    color: 'text.disabled',
                    '&:hover': { color: 'success.main' }
                  }}
                >
                  <HandThumbUpIcon sx={{ fontSize: 12 }} />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => {
                    onRate?.(message.id, 'thumbs_down')
                    setShowRating(true)
                  }}
                  sx={{ 
                    width: 24, 
                    height: 24, 
                    color: 'text.disabled',
                    '&:hover': { color: 'error.main' }
                  }}
                >
                  <HandThumbDownIcon sx={{ fontSize: 12 }} />
                </IconButton>
              </Box>
            </Box>
          )}
        </Box>

        {/* Suggestions */}
        {!isUser && message.metadata?.suggestions && message.metadata.suggestions.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
              Sugestões:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {message.metadata.suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outlined"
                  size="small"
                  onClick={() => onCopy?.(suggestion)}
                  sx={{ fontSize: '0.75rem', height: 24 }}
                >
                  {suggestion}
                </Button>
              ))}
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  )
}
