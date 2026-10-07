'use client'

import React, { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material'
import { CheckCircle, Business } from '@mui/icons-material'
import { AccountFormData } from './RegisterAccountForm'
import { TenantSearchResult } from '@/types'
import { hashString } from '@/utils/hash'

interface RegisterConfirmProps {
  accountData: AccountFormData
  selectedCartorio: TenantSearchResult | null
  cartorioRequested: boolean
  onSubmit: (data: {
    email: string
    first_name: string
    last_name: string
    password: string
    cartorio_id?: string | null
    cpf_hash?: string
    phone_hash?: string
  }) => Promise<void>
  isLoading?: boolean
  error?: string | null
}

export function RegisterConfirm({
  accountData,
  selectedCartorio,
  cartorioRequested,
  onSubmit,
  isLoading = false,
  error,
}: RegisterConfirmProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      // Hash CPF and phone client-side if provided
      let cpfHash: string | undefined
      let phoneHash: string | undefined

      if (accountData.cpf?.trim()) {
        cpfHash = await hashString(accountData.cpf.trim())
      }

      if (accountData.phone?.trim()) {
        phoneHash = await hashString(accountData.phone.trim())
      }

      await onSubmit({
        email: accountData.email,
        first_name: accountData.first_name,
        last_name: accountData.last_name,
        password: accountData.password,
        cartorio_id: selectedCartorio?.id || null,
        cpf_hash: cpfHash,
        phone_hash: phoneHash,
      })
    } catch (err) {
      console.error('Error submitting registration:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const displayName = `${accountData.first_name} ${accountData.last_name}`

  return (
    <Box sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Confirme seus dados
        </Typography>

        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <CheckCircle color="primary" />
              <Typography variant="subtitle1" fontWeight="bold">
                Conta
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2">
                <strong>Nome:</strong> {displayName}
              </Typography>
              <Typography variant="body2">
                <strong>Email:</strong> {accountData.email}
              </Typography>
            </Box>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Business color="primary" />
              <Typography variant="subtitle1" fontWeight="bold">
                Cartório
              </Typography>
            </Box>
            {selectedCartorio ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="body2">
                  <strong>Nome:</strong> {selectedCartorio.nome}
                </Typography>
                <Typography variant="body2">
                  <strong>Município:</strong> {selectedCartorio.municipio}
                </Typography>
                <Typography variant="body2">
                  <strong>UF:</strong> {selectedCartorio.uf}
                </Typography>
                {selectedCartorio.tipo && (
                  <Typography variant="body2">
                    <strong>Tipo:</strong> {selectedCartorio.tipo}
                  </Typography>
                )}
              </Box>
            ) : cartorioRequested ? (
              <Typography variant="body2" color="text.secondary">
                Solicitação de inclusão do cartório enviada
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Nenhum cartório selecionado
              </Typography>
            )}
          </CardContent>
        </Card>

        <Divider />

        <Button
          variant="contained"
          size="large"
          fullWidth
          onClick={handleSubmit}
          disabled={isLoading || isSubmitting}
          sx={{
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
          }}
        >
          {isLoading || isSubmitting ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={20} color="inherit" />
              Criando conta...
            </Box>
          ) : (
            'Criar conta'
          )}
        </Button>
      </Box>
    </Box>
  )
}

