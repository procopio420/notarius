'use client'

import React from 'react'
import { TextField } from '@mui/material'

interface VariableInputProps {
  variable: {
    name: string
    placeholder: string
    value: string
    isPII: boolean
  }
  showRealValues: boolean
  onChange: (variableName: string, newValue: string) => void
}

export function VariableInput({ variable, showRealValues, onChange }: VariableInputProps) {
  // Regular input for all variables (including RG and CPF)
  return (
    <TextField
      label={variable.name}
      value={showRealValues ? variable.value : variable.placeholder}
      onChange={(e) => onChange(variable.name, e.target.value)}
      fullWidth
      size="small"
      margin="dense"
      placeholder={variable.placeholder}
    />
  )
}
