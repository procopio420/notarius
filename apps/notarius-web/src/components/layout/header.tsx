'use client'

import { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Box,
  TextField,
  IconButton,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Typography,
  Divider,
  ListItemIcon,
  ListItemText,
  InputAdornment,
  Paper,
  List,
  ListItem,
  ListItemButton,
  Button,
} from '@mui/material'
import {
  Notifications as BellIcon,
  Search as MagnifyingGlassIcon,
  AccountCircle as UserCircleIcon,
  KeyboardArrowDown as ChevronDownIcon,
  Settings as Cog6ToothIcon,
  Logout as ArrowRightOnRectangleIcon,
} from '@mui/icons-material'
import { TenantSelector } from './TenantSelector'
import { useLogout } from '@/hooks/api/useAuth'
import { useAuthStore } from '@/store/slices/authSlice'

interface HeaderProps {
  className?: string
}

export function Header({ className }: HeaderProps) {
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null)
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null)
  const logoutMutation = useLogout()
  const { user } = useAuthStore()

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget)
  }

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null)
  }

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget)
  }

  const handleNotificationClose = () => {
    setNotificationAnchor(null)
  }

  const handleLogout = () => {
    logoutMutation.mutate()
    handleUserMenuClose()
  }

  const userDisplayName = user?.first_name && user?.last_name 
    ? `${user.first_name} ${user.last_name}`
    : user?.username || 'User'

  return (
    <AppBar 
      position="static" 
      elevation={1}
      sx={{ 
        backgroundColor: 'background.paper',
        color: 'text.primary',
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, sm: 3 } }}>
        {/* Search */}
        <Box sx={{ flexGrow: 1, maxWidth: 600, mr: 3 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Buscar documentos, processos..."
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <MagnifyingGlassIcon color="action" />
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'background.default',
              },
            }}
          />
        </Box>

        {/* Right side */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Tenant Selector */}
          <TenantSelector />
          
          {/* Notifications */}
          <IconButton
            onClick={handleNotificationOpen}
            color="inherit"
          >
            <Badge badgeContent={5} color="error">
              <BellIcon />
            </Badge>
          </IconButton>

          <Menu
            anchorEl={notificationAnchor}
            open={Boolean(notificationAnchor)}
            onClose={handleNotificationClose}
            PaperProps={{
              sx: { width: 320, maxHeight: 400 }
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6" component="h3">
                Notificações
              </Typography>
            </Box>
            <List sx={{ maxHeight: 300, overflow: 'auto' }}>
              <ListItem disablePadding>
                <ListItemButton>
                  <ListItemText
                    primary="Nova assinatura pendente"
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Procuração de João Silva
                        </Typography>
                        <Typography variant="caption" color="text.disabled">
                          há 5 minutos
                        </Typography>
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton>
                  <ListItemText
                    primary="Documento pronto para retirada"
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Escritura de Compra e Venda
                        </Typography>
                        <Typography variant="caption" color="text.disabled">
                          há 1 hora
                        </Typography>
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton>
                  <ListItemText
                    primary="Tarefa atribuída"
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Revisar minuta v2.1
                        </Typography>
                        <Typography variant="caption" color="text.disabled">
                          há 2 horas
                        </Typography>
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            </List>
            <Divider />
            <Box sx={{ p: 1 }}>
              <Button fullWidth variant="text">
                Ver todas as notificações
              </Button>
            </Box>
          </Menu>

          {/* User menu */}
          <IconButton
            onClick={handleUserMenuOpen}
            color="inherit"
            sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              {userDisplayName.charAt(0).toUpperCase()}
            </Avatar>
            <Box sx={{ display: { xs: 'none', md: 'block' } }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {userDisplayName}
              </Typography>
            </Box>
            <ChevronDownIcon />
          </IconButton>

          <Menu
            anchorEl={userMenuAnchor}
            open={Boolean(userMenuAnchor)}
            onClose={handleUserMenuClose}
            PaperProps={{
              sx: { width: 240 }
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {userDisplayName}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user?.email}
              </Typography>
            </Box>
            <MenuItem onClick={handleUserMenuClose}>
              <ListItemIcon>
                <UserCircleIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Perfil</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleUserMenuClose}>
              <ListItemIcon>
                <Cog6ToothIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Configurações</ListItemText>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout} disabled={logoutMutation.isPending}>
              <ListItemIcon>
                <ArrowRightOnRectangleIcon fontSize="small" color="error" />
              </ListItemIcon>
              <ListItemText>
                {logoutMutation.isPending ? 'Saindo...' : 'Sair'}
              </ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  )
}
