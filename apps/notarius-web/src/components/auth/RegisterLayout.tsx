'use client'

import React, { useState } from 'react'
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Typography,
  Alert,
} from '@mui/material'
import { RegisterAccountForm, AccountFormData } from './RegisterAccountForm'
import { RegisterCartorioSelect } from './RegisterCartorioSelect'
import { RegisterConfirm } from './RegisterConfirm'
import { TenantSearchResult } from '@/types'
import { useAuthStore } from '@/store/slices/authSlice'
import { useRouter } from 'next/navigation'

const steps = ['Conta', 'Cartório', 'Confirmação']

export function RegisterLayout() {
  const [activeStep, setActiveStep] = useState(0)
  const [accountData, setAccountData] = useState<AccountFormData | null>(null)
  const [selectedCartorio, setSelectedCartorio] = useState<TenantSearchResult | null>(null)
  const [cartorioRequested, setCartorioRequested] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { register: registerUser } = useAuthStore()
  const router = useRouter()

  const handleAccountSubmit = (data: AccountFormData) => {
    setAccountData(data)
    setError(null)
    setActiveStep(1)
  }

  const handleCartorioSelect = (cartorio: TenantSearchResult | null) => {
    if (cartorio) {
      setSelectedCartorio(cartorio)
      setError(null)
      setActiveStep(2)
    }
  }

  const handleCartorioRequestNew = () => {
    setCartorioRequested(true)
    setSelectedCartorio(null)
    setError(null)
    setActiveStep(2)
  }

  const handleRegisterSubmit = async (data: {
    email: string
    first_name: string
    last_name: string
    password: string
    cartorio_id?: string | null
    cpf_hash?: string
    phone_hash?: string
  }) => {
    try {
      setError(null)
      const result = await registerUser(data)
      // Redirect based on response status
      if (result?.redirect) {
        router.push(result.redirect)
      } else if (result?.status === 'ACTIVE') {
        router.push('/inbox')
      } else if (result?.status === 'NO_CARTORIO') {
        router.push('/onboarding/pending-cartorio')
      } else {
        // Default fallback - check if we have a cartorio
        if (selectedCartorio) {
          router.push('/inbox')
        } else {
          router.push('/onboarding/pending-cartorio')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar conta. Tente novamente.')
    }
  }

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1)
      setError(null)
    }
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mt: 4 }}>
        {activeStep === 0 && (
          <RegisterAccountForm
            onSubmit={handleAccountSubmit}
            isLoading={false}
            error={error}
          />
        )}

        {activeStep === 1 && (
          <RegisterCartorioSelect
            onSelect={handleCartorioSelect}
            onRequestNew={handleCartorioRequestNew}
            isLoading={false}
            error={error}
          />
        )}

        {activeStep === 2 && accountData && (
          <RegisterConfirm
            accountData={accountData}
            selectedCartorio={selectedCartorio}
            cartorioRequested={cartorioRequested}
            onSubmit={handleRegisterSubmit}
            isLoading={false}
            error={error}
          />
        )}
      </Box>
    </Box>
  )
}

