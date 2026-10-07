'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  TextField,
  Button,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Visibility, VisibilityOff } from '@mui/icons-material'

const accountSchema = z.object({
  email: z.string().email('Email inválido'),
  first_name: z.string().min(2, 'Nome deve ter pelo menos 2 caracteres'),
  last_name: z.string().min(2, 'Sobrenome deve ter pelo menos 2 caracteres'),
  password: z.string().min(6, 'Senha deve ter pelo menos 6 caracteres'),
  cpf: z.string().optional(),
  phone: z.string().optional(),
})

export type AccountFormData = z.infer<typeof accountSchema>

interface RegisterAccountFormProps {
  onSubmit: (data: AccountFormData) => void
  isLoading?: boolean
  error?: string | null
}

export function RegisterAccountForm({
  onSubmit,
  isLoading = false,
  error,
}: RegisterAccountFormProps) {
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AccountFormData>({
    resolver: zodResolver(accountSchema),
  })

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <TextField
          {...register('email')}
          label="Email"
          type="email"
          variant="outlined"
          fullWidth
          required
          error={!!errors.email}
          helperText={errors.email?.message}
          disabled={isLoading}
          autoComplete="email"
          aria-label="Email"
        />

        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            {...register('first_name')}
            label="Nome"
            variant="outlined"
            fullWidth
            required
            error={!!errors.first_name}
            helperText={errors.first_name?.message}
            disabled={isLoading}
            autoComplete="given-name"
            aria-label="Nome"
          />
          <TextField
            {...register('last_name')}
            label="Sobrenome"
            variant="outlined"
            fullWidth
            required
            error={!!errors.last_name}
            helperText={errors.last_name?.message}
            disabled={isLoading}
            autoComplete="family-name"
            aria-label="Sobrenome"
          />
        </Box>

        <TextField
          {...register('password')}
          label="Senha"
          type={showPassword ? 'text' : 'password'}
          variant="outlined"
          fullWidth
          required
          error={!!errors.password}
          helperText={errors.password?.message}
          disabled={isLoading}
          autoComplete="new-password"
          aria-label="Senha"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                  disabled={isLoading}
                  aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            {...register('cpf')}
            label="CPF (opcional)"
            variant="outlined"
            fullWidth
            error={!!errors.cpf}
            helperText={errors.cpf?.message || 'Será criptografado localmente'}
            disabled={isLoading}
            placeholder="000.000.000-00"
            aria-label="CPF (opcional)"
          />
          <TextField
            {...register('phone')}
            label="Telefone (opcional)"
            variant="outlined"
            fullWidth
            error={!!errors.phone}
            helperText={errors.phone?.message || 'Será criptografado localmente'}
            disabled={isLoading}
            placeholder="(11) 99999-9999"
            aria-label="Telefone (opcional)"
          />
        </Box>

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
          }}
        >
          Continuar
        </Button>
      </Box>
    </Box>
  )
}

