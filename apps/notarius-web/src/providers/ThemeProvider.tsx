'use client'

import { useEffect, useState } from 'react'
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { theme } from '@/theme'

interface ThemeProviderProps {
  children: React.ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  // Match the protected route's server/first-client loading view. Emotion's
  // global baseline is installed after hydration instead of occupying that
  // view's first DOM node with a server-only style element.
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])
  return (
    <MuiThemeProvider theme={theme}>
      {mounted && <CssBaseline />}
      {children}
    </MuiThemeProvider>
  )
}
