'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  IconButton,
  Badge,
  Avatar,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Description as DocumentTextIcon,
  Settings as CogIcon,
  Group as UserGroupIcon,
  BarChart as ChartBarIcon,
  Notifications as BellIcon,
  Assignment as ClipboardDocumentListIcon,
  FileCopy as DocumentDuplicateIcon,
  AutoAwesome as SparklesIcon,
  Security as ShieldCheckIcon,
  Mail as EnvelopeIcon,
  Queue as QueueListIcon,
  Person as UserIcon,
  Home as HomeIcon,
  Menu as Bars3Icon,
  Close as XMarkIcon,
  Edit as PencilIcon,
} from '@mui/icons-material'

const navigation = [
  { name: 'Inbox', href: '/inbox', icon: EnvelopeIcon },
  { name: 'Criar do Prompt', href: '/criar', icon: PencilIcon },
  { name: 'Processos', href: '/processos', icon: ClipboardDocumentListIcon },
  { name: 'Minutas', href: '/minutas', icon: DocumentTextIcon },
  { name: 'Documentos', href: '/documentos', icon: DocumentDuplicateIcon },
  { name: 'Assistente', href: '/assistente', icon: SparklesIcon },
]

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'))

  const drawerWidth = 280

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              bgcolor: 'primary.main',
              width: 40,
              height: 40,
              fontSize: '1.2rem',
              fontWeight: 'bold',
            }}
          >
            N
          </Avatar>
          <Box>
            <Typography variant="h6" component="h1" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
              Notarius
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.2 }}>
              Cartório Digital
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ px: 1, py: 2 }}>
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <ListItem key={item.name} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  component={Link}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  sx={{
                    borderRadius: 2,
                    mx: 1,
                    '&.Mui-selected': {
                      backgroundColor: 'primary.light',
                      color: 'primary.contrastText',
                      '&:hover': {
                        backgroundColor: 'primary.main',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'primary.contrastText',
                      },
                    },
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                  selected={isActive}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 40,
                      color: isActive ? 'primary.contrastText' : 'text.secondary',
                    }}
                  >
                    <item.icon />
                  </ListItemIcon>
                  <ListItemText
                    primary={item.name}
                    primaryTypographyProps={{
                      fontSize: '0.95rem',
                      fontWeight: isActive ? 600 : 400,
                    }}
                  />
                  {(item.name === 'Tarefas' || item.name === 'Notificações') && (
                    <Badge
                      badgeContent={item.name === 'Tarefas' ? 3 : 5}
                      color="error"
                      sx={{ ml: 1 }}
                    />
                  )}
                </ListItemButton>
              </ListItem>
            )
          })}
        </List>
      </Box>
    </Box>
  )

  return (
    <>
      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', lg: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundColor: 'background.paper',
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop Drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', lg: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundColor: 'background.paper',
            borderRight: 1,
            borderColor: 'divider',
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>

      {/* Mobile menu button */}
      {isMobile && (
        <IconButton
          onClick={() => setSidebarOpen(true)}
          sx={{
            position: 'fixed',
            top: 16,
            left: 16,
            zIndex: theme.zIndex.drawer + 1,
            backgroundColor: 'background.paper',
            boxShadow: 2,
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        >
          <Bars3Icon />
        </IconButton>
      )}
    </>
  )
}
