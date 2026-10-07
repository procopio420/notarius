'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Box,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material'
import { Search as SearchIcon } from '@mui/icons-material'
import { TenantSearchResult, TenantRequest } from '@/types'

const BRAZILIAN_STATES = [
  { code: 'AC', name: 'Acre' },
  { code: 'AL', name: 'Alagoas' },
  { code: 'AP', name: 'Amapá' },
  { code: 'AM', name: 'Amazonas' },
  { code: 'BA', name: 'Bahia' },
  { code: 'CE', name: 'Ceará' },
  { code: 'DF', name: 'Distrito Federal' },
  { code: 'ES', name: 'Espírito Santo' },
  { code: 'GO', name: 'Goiás' },
  { code: 'MA', name: 'Maranhão' },
  { code: 'MT', name: 'Mato Grosso' },
  { code: 'MS', name: 'Mato Grosso do Sul' },
  { code: 'MG', name: 'Minas Gerais' },
  { code: 'PA', name: 'Pará' },
  { code: 'PB', name: 'Paraíba' },
  { code: 'PR', name: 'Paraná' },
  { code: 'PE', name: 'Pernambuco' },
  { code: 'PI', name: 'Piauí' },
  { code: 'RJ', name: 'Rio de Janeiro' },
  { code: 'RN', name: 'Rio Grande do Norte' },
  { code: 'RS', name: 'Rio Grande do Sul' },
  { code: 'RO', name: 'Rondônia' },
  { code: 'RR', name: 'Roraima' },
  { code: 'SC', name: 'Santa Catarina' },
  { code: 'SP', name: 'São Paulo' },
  { code: 'SE', name: 'Sergipe' },
  { code: 'TO', name: 'Tocantins' },
]

interface RegisterCartorioSelectProps {
  onSelect: (cartorio: TenantSearchResult | null) => void
  onRequestNew: () => void
  isLoading?: boolean
  error?: string | null
}

export function RegisterCartorioSelect({
  onSelect,
  onRequestNew,
  isLoading = false,
  error,
}: RegisterCartorioSelectProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedUF, setSelectedUF] = useState<string>('')
  const [results, setResults] = useState<TenantSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [showRequestDialog, setShowRequestDialog] = useState(false)
  const [requestData, setRequestData] = useState<TenantRequest>({
    nome: '',
    municipio: '',
    uf: '',
    note: '',
  })
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

  const searchTenants = useCallback(async (query: string, uf?: string) => {
    if (!query.trim()) {
      setResults([])
      return
    }

    setIsSearching(true)
    try {
      const params = new URLSearchParams({ q: query, limit: '20' })
      if (uf) {
        params.append('uf', uf)
      }

      const response = await fetch(`${API_URL}/v1/tenancy/tenants/search/?${params}`)
      if (!response.ok) {
        throw new Error('Erro ao buscar cartórios')
      }

      const data = await response.json()
      setResults(data)
      setSelectedIndex(-1)
    } catch (err) {
      console.error('Error searching tenants:', err)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }, [API_URL])

  useEffect(() => {
    // Debounce search
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    searchTimeoutRef.current = setTimeout(() => {
      if (searchTerm.trim()) {
        searchTenants(searchTerm, selectedUF || undefined)
      } else {
        setResults([])
      }
    }, 280)

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchTerm, selectedUF, searchTenants])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (results.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) =>
          prev < results.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex])
        }
        break
    }
  }

  const handleSelect = (cartorio: TenantSearchResult) => {
    onSelect(cartorio)
  }

  const handleRequestNew = () => {
    setShowRequestDialog(true)
  }

  const handleSubmitRequest = async () => {
    if (!requestData.nome || !requestData.municipio || !requestData.uf) {
      setRequestError('Por favor, preencha todos os campos obrigatórios')
      return
    }

    setIsSubmittingRequest(true)
    setRequestError(null)

    try {
      const response = await fetch(`${API_URL}/v1/tenancy/tenants/request-new/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao solicitar inclusão')
      }

      const result = await response.json()
      setShowRequestDialog(false)
      setRequestData({ nome: '', municipio: '', uf: '', note: '' })
      onRequestNew()
    } catch (err) {
      setRequestError(err instanceof Error ? err.message : 'Erro ao solicitar inclusão')
    } finally {
      setIsSubmittingRequest(false)
    }
  }

  return (
    <Box sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Selecione o cartório onde você trabalha
        </Typography>

        <FormControl fullWidth>
          <InputLabel id="uf-select-label">Estado (UF)</InputLabel>
          <Select
            labelId="uf-select-label"
            value={selectedUF}
            label="Estado (UF)"
            onChange={(e) => setSelectedUF(e.target.value)}
            disabled={isLoading}
          >
            <MenuItem value="">Todos</MenuItem>
            {BRAZILIAN_STATES.map((state) => (
              <MenuItem key={state.code} value={state.code}>
                {state.code} - {state.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          label="Buscar cartório"
          variant="outlined"
          fullWidth
          placeholder="Digite o nome do cartório ou município"
          disabled={isLoading}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            endAdornment: isSearching && <CircularProgress size={20} />,
          }}
          aria-label="Buscar cartório"
        />

        {results.length > 0 && (
          <Paper
            ref={listRef}
            elevation={3}
            sx={{
              maxHeight: 300,
              overflow: 'auto',
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <List dense>
              {results.map((tenant, index) => (
                <ListItem
                  key={tenant.id}
                  button
                  selected={index === selectedIndex}
                  onClick={() => handleSelect(tenant)}
                  sx={{
                    '&:hover': { backgroundColor: 'action.hover' },
                    '&.Mui-selected': { backgroundColor: 'action.selected' },
                  }}
                >
                  <ListItemText
                    primary={tenant.nome}
                    secondary={
                      <>
                        {tenant.municipio && `${tenant.municipio}, `}
                        {tenant.uf}
                        {tenant.tipo && ` • ${tenant.tipo}`}
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        )}

        {!isSearching && searchTerm && results.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Nenhum cartório encontrado
            </Typography>
            <Button
              variant="outlined"
              onClick={handleRequestNew}
              disabled={isLoading}
            >
              Solicitar inclusão do cartório
            </Button>
          </Box>
        )}

        {!searchTerm && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Digite o nome do cartório para buscar
          </Typography>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
          Esta informação pode ser verificada posteriormente.
        </Typography>
      </Box>

      <Dialog open={showRequestDialog} onClose={() => setShowRequestDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Solicitar inclusão do cartório</DialogTitle>
        <DialogContent>
          {requestError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {requestError}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Nome do cartório"
              fullWidth
              required
              value={requestData.nome}
              onChange={(e) => setRequestData({ ...requestData, nome: e.target.value })}
              disabled={isSubmittingRequest}
            />
            <TextField
              label="Município"
              fullWidth
              required
              value={requestData.municipio}
              onChange={(e) => setRequestData({ ...requestData, municipio: e.target.value })}
              disabled={isSubmittingRequest}
            />
            <FormControl fullWidth required>
              <InputLabel>Estado (UF)</InputLabel>
              <Select
                value={requestData.uf}
                label="Estado (UF)"
                onChange={(e) => setRequestData({ ...requestData, uf: e.target.value })}
                disabled={isSubmittingRequest}
              >
                {BRAZILIAN_STATES.map((state) => (
                  <MenuItem key={state.code} value={state.code}>
                    {state.code} - {state.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Observação (opcional)"
              fullWidth
              multiline
              rows={3}
              value={requestData.note}
              onChange={(e) => setRequestData({ ...requestData, note: e.target.value })}
              disabled={isSubmittingRequest}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowRequestDialog(false)} disabled={isSubmittingRequest}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmitRequest}
            variant="contained"
            disabled={isSubmittingRequest || !requestData.nome || !requestData.municipio || !requestData.uf}
          >
            {isSubmittingRequest ? <CircularProgress size={20} /> : 'Enviar solicitação'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

