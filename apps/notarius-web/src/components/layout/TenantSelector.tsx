'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTenantStore } from '@/store/slices/tenantSlice'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'
import {
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  CircularProgress,
} from '@mui/material'
import { KeyboardArrowDown as ChevronDownIcon, Business as BusinessIcon } from '@mui/icons-material'

interface Tenant {
  id: string
  nome: string
  cnpj: string
  uf: string
  cidade: string
  endereco: string
  telefone: string
  email: string
  is_active: boolean
}

export function TenantSelector() {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const { selectedTenant, setSelectedTenant } = useTenantStore()

  const { data: tenants = [], isLoading } = useQuery({
    queryKey: queryKeys.tenants.list(),
    queryFn: async (): Promise<Tenant[]> => {
      const response = await api.get('/api/v1/tenants/')
      return response.data.results || response.data
    },
    // Always fetch tenants so we can select one
  })

  // Auto-select first tenant if none is selected
  useEffect(() => {
    if (tenants.length > 0 && !selectedTenant) {
      setSelectedTenant(tenants[0])
    }
  }, [tenants, selectedTenant, setSelectedTenant])

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleTenantSelect = (tenant: Tenant) => {
    setSelectedTenant(tenant)
    handleClose()
  }

  if (isLoading) {
    return (
      <Button variant="outlined" disabled startIcon={<CircularProgress size={16} />}>
        Carregando...
      </Button>
    )
  }

  return (
    <>
      <Button
        variant="outlined"
        onClick={handleClick}
        endIcon={<ChevronDownIcon />}
        sx={{ minWidth: 200, justifyContent: 'space-between' }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, overflow: 'hidden' }}>
          <BusinessIcon sx={{ fontSize: 16, flexShrink: 0 }} />
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {selectedTenant?.nome || 'Selecionar Cartório'}
          </Typography>
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: { minWidth: 280, maxHeight: 400 }
        }}
      >
        {tenants.length === 0 ? (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              Nenhum cartório disponível
            </Typography>
          </MenuItem>
        ) : (
          tenants.map((tenant) => (
            <MenuItem
              key={tenant.id}
              onClick={() => handleTenantSelect(tenant)}
              selected={selectedTenant?.id === tenant.id}
            >
              <ListItemIcon>
                <BusinessIcon />
              </ListItemIcon>
              <ListItemText
                primary={tenant.nome}
                secondary={`${tenant.cidade}, ${tenant.uf}`}
              />
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  )
}

