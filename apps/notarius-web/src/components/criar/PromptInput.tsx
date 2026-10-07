'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, TextField, Box, Typography, CircularProgress } from '@mui/material'
import { AutoAwesome as SparklesIcon } from '@mui/icons-material'

const promptSchema = z.object({
  command: z.string().min(10, 'Descrição deve ter pelo menos 10 caracteres'),
})

type PromptFormData = z.infer<typeof promptSchema>

interface PromptInputProps {
  onSubmit: (command: string) => void
  isLoading: boolean
  defaultValue?: string
}

export function PromptInput({ onSubmit, isLoading, defaultValue = '' }: PromptInputProps) {
  const [charCount, setCharCount] = useState(defaultValue.length)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<PromptFormData>({
    resolver: zodResolver(promptSchema),
    defaultValues: { command: defaultValue },
  })

  const commandValue = watch('command')

  const handleFormSubmit = (data: PromptFormData) => {
    onSubmit(data.command)
  }

  const handleClear = () => {
    reset()
    setCharCount(0)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCharCount(e.target.value.length)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box>
        <Typography variant="h4" component="h2" sx={{ fontWeight: 600, mb: 1 }}>
          Criar do Prompt
        </Typography>
        <Typography color="text.secondary">
          Descreva o processo desejado e nossa IA irá estruturar automaticamente as partes, dados e checklist necessários.
        </Typography>
      </Box>

      <Box component="form" onSubmit={handleSubmit(handleFormSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Box>
          <TextField
            {...register('command')}
            onChange={(e) => {
              register('command').onChange(e)
              handleInputChange(e)
            }}
            autoFocus
            multiline
            rows={5}
            fullWidth
            label="Descrição do Processo"
            placeholder="Ex.: Procuração para venda de imóvel. Outorgante: João da Silva, CPF 123.456.789-00; Outorgado: Maria Souza, CPF 987.654.321-00. Imóvel em SP. Válida por 90 dias."
            disabled={isLoading}
            error={!!errors.command}
            helperText={errors.command?.message}
            sx={{
              '& .MuiInputBase-input': {
                resize: 'none'
              }
            }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {charCount} caracteres
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            type="submit"
            variant="contained"
            disabled={isLoading || !commandValue || commandValue.length < 10}
            startIcon={isLoading ? <CircularProgress size={16} /> : <SparklesIcon />}
            sx={{
              background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1565c0 30%, #1976d2 90%)',
              }
            }}
          >
            {isLoading ? 'Analisando...' : 'Analisar'}
          </Button>
          
          <Button
            type="button"
            variant="outlined"
            onClick={handleClear}
            disabled={isLoading}
          >
            Limpar
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

