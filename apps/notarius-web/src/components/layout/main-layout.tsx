'use client'

import { Sidebar } from './sidebar'
import { Header } from './header'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Box, useTheme, useMediaQuery } from '@mui/material'

interface MainLayoutProps {
  children: React.ReactNode
  hideSidebar?: boolean
  hideHeader?: boolean
}

export function MainLayout({ children, hideSidebar = false, hideHeader = false }: MainLayoutProps) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'))
  const drawerWidth = 280

  return (
    <ProtectedRoute>
      <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
        {!hideSidebar && <Sidebar />}
        
        {/* Main content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            ml: { lg: hideSidebar ? 0 : `${drawerWidth}px` },
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {!hideHeader && <Header />}
          
          <Box
            sx={{
              flexGrow: 1,
              p: { xs: 2, sm: 3 },
              backgroundColor: 'background.default',
            }}
          >
            {children}
          </Box>
        </Box>
      </Box>
    </ProtectedRoute>
  )
}