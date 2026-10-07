'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/slices/authSlice'
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
  CircularProgress,
  Grid,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Visibility, VisibilityOff } from '@mui/icons-material'

const registerSchema = z.object({
  username: z.string().min(2, 'Usuário deve ter pelo menos 2 caracteres'),
  email: z.string().email('Email inválido'),
  password: z.string().min(6, 'Senha deve ter pelo menos 6 caracteres'),
  confirm_password: z.string(),
  first_name: z.string().min(2, 'Nome deve ter pelo menos 2 caracteres'),
  last_name: z.string().min(2, 'Sobrenome deve ter pelo menos 2 caracteres'),
  cpf: z.string().min(11, 'CPF deve ter 11 dígitos'),
  phone: z.string().min(10, 'Telefone inválido'),
}).refine((data) => data.password === data.confirm_password, {
  message: "Senhas não coincidem",
  path: ["confirm_password"],
})

type RegisterFormData = z.infer<typeof registerSchema>

export function RegisterForm() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { register: registerUser } = useAuthStore()
  const router = useRouter()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true)
    setError(null)

    try {
      await registerUser({
        username: data.username,
        email: data.email,
        password: data.password,
        confirm_password: data.confirm_password,
        first_name: data.first_name,
        last_name: data.last_name,
        cpf: data.cpf,
        phone: data.phone,
      })
      
      router.push('/inbox')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao criar conta. Tente novamente.')
    } finally {
      setIsLoading(false)
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
          disabled={isLoading}
        />

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField
              {...register('first_name')}
              label="Nome"
              variant="outlined"
              fullWidth
              error={!!errors.first_name}
              helperText={errors.first_name?.message}
              disabled={isLoading}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              {...register('last_name')}
              label="Sobrenome"
              variant="outlined"
              fullWidth
              error={!!errors.last_name}
              helperText={errors.last_name?.message}
              disabled={isLoading}
            />
          </Grid>
        </Grid>

        <TextField
          {...register('email')}
          label="Email"
          type="email"
          variant="outlined"
          fullWidth
          error={!!errors.email}
          helperText={errors.email?.message}
          disabled={isLoading}
        />

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField
              {...register('cpf')}
              label="CPF"
              variant="outlined"
              fullWidth
              error={!!errors.cpf}
              helperText={errors.cpf?.message}
              disabled={isLoading}
              placeholder="000.000.000-00"
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              {...register('phone')}
              label="Telefone"
              variant="outlined"
              fullWidth
              error={!!errors.phone}
              helperText={errors.phone?.message}
              disabled={isLoading}
              placeholder="(11) 99999-9999"
            />
          </Grid>
        </Grid>

        <TextField
          {...register('password')}
          label="Senha"
          type={showPassword ? 'text' : 'password'}
          variant="outlined"
          fullWidth
          error={!!errors.password}
          helperText={errors.password?.message}
          disabled={isLoading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                  disabled={isLoading}
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <TextField
          {...register('confirm_password')}
          label="Confirmar Senha"
          type={showConfirmPassword ? 'text' : 'password'}
          variant="outlined"
          fullWidth
          error={!!errors.confirm_password}
          helperText={errors.confirm_password?.message}
          disabled={isLoading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  edge="end"
                  disabled={isLoading}
                >
                  {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Button
          type="submit"
          variant="contained"
          size="large"
          fullWidth
          disabled={isLoading}
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
          {isLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={20} color="inherit" />
              Criando conta...
            </Box>
          ) : (
            'Criar Conta'
          )}
        </Button>
      </Box>

      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Já tem uma conta?{' '}
          <Link
            href="/login"
            sx={{
              fontWeight: 600,
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            Faça login
          </Link>
        </Typography>
      </Box>
    </Box>
  )
}