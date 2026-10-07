'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useLogin } from '@/hooks/api/useAuth'
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
  CircularProgress,
} from '@mui/material'

const loginSchema = z.object({
  username: z.string().min(1, 'Usuário é obrigatório'),
  password: z.string().min(1, 'Senha é obrigatória'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginForm() {
  const router = useRouter()
  const loginMutation = useLogin()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setError(null)
    try {
      await loginMutation.mutateAsync(data)
      router.push('/inbox')
    } catch (err: unknown) {
      const errorMessage = err instanceof Error && 'response' in err 
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Falha no login. Tente novamente.'
        : 'Falha no login. Tente novamente.'
      setError(errorMessage)
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <TextField
          {...register('username')}
          label="Usuário"
          variant="outlined"
          fullWidth
          error={!!errors.username}
          helperText={errors.username?.message}
          disabled={loginMutation.isPending}
        />

        <TextField
          {...register('password')}
          label="Senha"
          type="password"
          variant="outlined"
          fullWidth
          error={!!errors.password}
          helperText={errors.password?.message}
          disabled={loginMutation.isPending}
        />

        <Button
          type="submit"
          variant="contained"
          size="large"
          fullWidth
          disabled={loginMutation.isPending}
          sx={{
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1565c0, #1976d2)',
            },
          }}
        >
          {loginMutation.isPending ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={20} color="inherit" />
              Entrando...
            </Box>
          ) : (
            'Entrar'
          )}
        </Button>
      </Box>

      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Não tem uma conta?{' '}
          <Link
            href="/register"
            sx={{
              fontWeight: 600,
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            Criar conta
          </Link>
        </Typography>
      </Box>
    </Box>
  )
}
