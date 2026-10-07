'use client'

import { LoginForm } from '@/components/auth/LoginForm'
import { PageLoader } from '@/components/common/PageLoader'
import { useAuthStore } from '@/store/slices/authSlice'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Box, Container, Typography, Avatar, Paper } from '@mui/material'
import { Description as DescriptionIcon } from '@mui/icons-material'

export default function LoginPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/inbox')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return <PageLoader message="Verificando autenticação..." />
  }

  if (isAuthenticated) {
    return <PageLoader message="Redirecionando..." />
  }

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
            <Avatar
              sx={{
                width: 80,
                height: 80,
                mx: 'auto',
                mb: 2,
                background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
              }}
            >
              <DescriptionIcon sx={{ fontSize: 40 }} />
            </Avatar>
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
              Notarius
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Faça login em sua conta
            </Typography>
          </Box>
          
          <LoginForm />
        </Paper>
      </Container>
    </Box>
  )
}
