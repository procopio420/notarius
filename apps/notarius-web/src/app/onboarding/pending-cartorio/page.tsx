'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Box, Container, Typography, Paper, Button, Alert } from '@mui/material'
import { CheckCircle, ArrowBack } from '@mui/icons-material'
import { useAuthStore } from '@/store/slices/authSlice'

export default function PendingCartorioPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, router])

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 3,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            p: 4,
            borderRadius: 3,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
              Solicitação registrada
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Sua solicitação de cartório foi registrada com sucesso
            </Typography>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Nossa equipe irá revisar sua solicitação e entrar em contato em breve.
              Você receberá um email quando sua solicitação for processada.
            </Typography>
          </Alert>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={() => router.push('/app')}
              sx={{
                py: 1.5,
                fontSize: '1.1rem',
                fontWeight: 600,
              }}
            >
              Acessar aplicativo
            </Button>

            <Button
              variant="outlined"
              size="large"
              fullWidth
              startIcon={<ArrowBack />}
              onClick={() => router.push('/login')}
            >
              Voltar para login
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  )
}

