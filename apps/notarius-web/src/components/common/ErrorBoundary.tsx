'use client'

import React from 'react'
import { Button, Card, CardContent, CardHeader, Typography, Box } from '@mui/material'
import { Warning as ExclamationTriangleIcon, Refresh as ArrowPathIcon } from '@mui/icons-material'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({ error, errorInfo })
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />
      }

      return <DefaultErrorFallback error={this.state.error!} resetError={this.resetError} />
    }

    return this.props.children
  }
}

function DefaultErrorFallback({ error, resetError }: { error: Error; resetError: () => void }) {
  return (
    <Box sx={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      bgcolor: 'grey.50' 
    }}>
      <Card sx={{ maxWidth: 448, width: '100%', mx: 2 }}>
        <CardHeader sx={{ textAlign: 'center' }}>
          <Box sx={{ 
            mx: 'auto', 
            width: 48, 
            height: 48, 
            bgcolor: 'error.50', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            mb: 2 
          }}>
            <ExclamationTriangleIcon sx={{ fontSize: 24, color: 'error.main' }} />
          </Box>
          <Typography variant="h5" sx={{ color: 'text.primary' }}>
            Algo deu errado
          </Typography>
        </CardHeader>
        <CardContent sx={{ textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Ocorreu um erro inesperado. Nossa equipe foi notificada e está trabalhando para resolver o problema.
          </Typography>
          
          {process.env.NODE_ENV === 'development' && (
            <Box sx={{ textAlign: 'left', mb: 3 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Detalhes do erro (desenvolvimento):
              </Typography>
              <Box sx={{ 
                mt: 1, 
                fontSize: '0.75rem', 
                color: 'error.main', 
                bgcolor: 'error.50', 
                p: 2, 
                borderRadius: 1, 
                overflow: 'auto',
                fontFamily: 'monospace'
              }}>
                {error.message}
                {error.stack && `\n\n${error.stack}`}
              </Box>
            </Box>
          )}
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="outlined"
              onClick={() => window.location.reload()}
              startIcon={<ArrowPathIcon />}
            >
              Recarregar Página
            </Button>
            <Button
              variant="contained"
              onClick={resetError}
            >
              Tentar Novamente
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
