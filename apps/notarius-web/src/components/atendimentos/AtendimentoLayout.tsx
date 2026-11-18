'use client'

import Link from 'next/link'
import { useId, useState, type ReactNode } from 'react'
import { Avatar, Box, Button, Divider, IconButton, ListItemIcon, Menu, MenuItem, Stack, ThemeProvider, Typography, createTheme } from '@mui/material'
import { ChevronDown, LogOut } from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { EspacoAutomatico } from './EspacoAutomatico'
import { useAuthStore } from '@/store/slices/authSlice'
import { useLogout } from '@/hooks/api/useAuth'

const atendimentoTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#254c40', light: '#eaf0e9', dark: '#17382d', contrastText: '#ffffff' },
    secondary: { main: '#d9edaa', contrastText: '#203c35' },
    text: { primary: '#203c35', secondary: '#6c7b73' },
    background: { default: '#f7f7f2', paper: '#ffffff' },
    divider: '#e3e8df',
    success: { main: '#3d7158' },
    warning: { main: '#946c24', light: '#faf4e7', dark: '#72511a' },
    info: { main: '#4e7064', light: '#f0f4ef', dark: '#345146' },
    error: { main: '#b34840' },
  },
  shape: { borderRadius: 6 },
  typography: {
    fontFamily: '"Inter", "Segoe UI", Arial, sans-serif',
    fontSize: 14,
    h1: { fontSize: '2.25rem', fontWeight: 650, letterSpacing: '-.055em', lineHeight: 1.15 },
    h2: { fontSize: '1.4rem', fontWeight: 650, letterSpacing: '-.035em', lineHeight: 1.3 },
    h3: { fontSize: '1.125rem', fontWeight: 650, letterSpacing: '-.02em' },
    h4: { fontSize: '1.75rem', fontWeight: 650, letterSpacing: '-.04em' },
    h5: { fontSize: '1.35rem', fontWeight: 650, letterSpacing: '-.03em' },
    h6: { fontSize: '1.1rem', fontWeight: 650, letterSpacing: '-.02em' },
    body1: { fontSize: '.9375rem', lineHeight: 1.65 },
    body2: { fontSize: '.875rem', lineHeight: 1.6 },
    caption: { fontSize: '.75rem', lineHeight: 1.5 },
    button: { fontSize: '.875rem', fontWeight: 600, textTransform: 'none' },
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { minHeight: 42, borderRadius: 10, padding: '9px 17px', textTransform: 'none', transition: 'background-color .18s ease, border-color .18s ease' },
        sizeSmall: { minHeight: 36, padding: '6px 12px' },
        outlined: { borderColor: '#dbe3d9', '&:hover': { borderColor: '#a6b9a7', backgroundColor: '#f3f6ef' } },
      },
    },
    MuiIconButton: { styleOverrides: { root: { '&:focus-visible': { outline: '3px solid #8aaf79', outlineOffset: 3 } } } },
    MuiPaper: { defaultProps: { elevation: 0 }, styleOverrides: { root: { backgroundImage: 'none' }, rounded: { borderRadius: 16 } } },
    MuiTextField: { defaultProps: { size: 'small' } },
    MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 10, backgroundColor: '#fff', '& .MuiOutlinedInput-notchedOutline': { borderColor: '#dce3da' }, '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#9caf9d' } }, input: { padding: '12px 14px', fontSize: '.9375rem' } } },
    MuiInputLabel: { styleOverrides: { root: { fontSize: '.9375rem' } } },
    MuiFormHelperText: { styleOverrides: { root: { marginLeft: 0, fontSize: '.75rem', lineHeight: 1.5 } } },
    MuiChip: { styleOverrides: { root: { fontSize: '.75rem', fontWeight: 600, borderRadius: 7, height: 27 } } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 12, alignItems: 'flex-start', fontSize: '.875rem' }, standardInfo: { backgroundColor: '#f0f4ef', color: '#426052' }, standardWarning: { backgroundColor: '#faf4e7', color: '#72551f' } } },
    MuiAccordion: { defaultProps: { disableGutters: true, elevation: 0 }, styleOverrides: { root: { border: '1px solid #e3e8df', borderRadius: '12px !important', '&::before': { display: 'none' }, '&.Mui-expanded': { margin: 0 } } } },
    MuiAccordionSummary: { styleOverrides: { root: { minHeight: 52, padding: '0 18px' }, content: { margin: '12px 0' } } },
    MuiAccordionDetails: { styleOverrides: { root: { padding: '0 18px 18px' } } },
    MuiTabs: { styleOverrides: { root: { minHeight: 48 }, indicator: { height: 2, borderRadius: 2 } } },
    MuiTab: { styleOverrides: { root: { minHeight: 48, textTransform: 'none', fontSize: '.875rem', fontWeight: 600 } } },
    MuiDialog: { styleOverrides: { paper: { borderRadius: 20, backgroundImage: 'none' } } },
    MuiDialogTitle: { styleOverrides: { root: { fontSize: '1.3rem', fontWeight: 650, padding: '24px 24px 12px' } } },
    MuiDialogActions: { styleOverrides: { root: { padding: '16px 24px 24px', gap: 8, flexWrap: 'wrap' } } },
    MuiMenu: { defaultProps: { slotProps: { paper: { sx: { mt: 1, border: '1px solid #e3e8df', boxShadow: '0 14px 40px #203c3514' } } } } },
  },
})

export function AtendimentoLayout({ children }: { children: ReactNode }) {
  const { user } = useAuthStore()
  const logout = useLogout()
  const [anchor, setAnchor] = useState<HTMLElement | null>(null)
  const menuId = useId()
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || 'Minha conta'
  const initial = name.slice(0, 1).toUpperCase()

  return <ThemeProvider theme={atendimentoTheme}>
    <ProtectedRoute>
      {process.env.NEXT_PUBLIC_PILOTO_LOCAL !== '1' && <EspacoAutomatico />}
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
        <Box component="a" href="#conteudo-atendimento" sx={{ position: 'absolute', top: 8, left: 12, zIndex: 1500, transform: 'translateY(-180%)', '&:focus': { transform: 'none' }, bgcolor: '#254c40', color: '#fff', px: 2, py: 1, borderRadius: 2 }}>Pular para o conteúdo</Box>
        <Box component="header" sx={{ bgcolor: '#ffffffed', borderBottom: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ maxWidth: 1280, mx: 'auto', minHeight: { xs: 68, sm: 76 }, px: { xs: 2.5, md: 5 }, display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 4 }, flexWrap: 'nowrap', py: { xs: 1, sm: 0 } }}>
            <Box component={Link} href="/atendimentos" aria-label="Notarius — início" sx={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 1.25, color: 'text.primary', flexShrink: 0 }}>
              <Box aria-hidden="true" sx={{ width: 35, height: 38, borderRadius: '10px 10px 10px 2px', bgcolor: '#254c40', display: 'grid', placeItems: 'center', fontFamily: 'Georgia, serif', fontSize: 25, fontWeight: 500, color: '#e1efbe' }}>N</Box>
              <Typography component="span" sx={{ fontFamily: 'Georgia, "Times New Roman", serif', fontSize: 25, letterSpacing: '-1px', fontWeight: 500 }}>notarius<span style={{ color: '#6e8a55' }}>.</span></Typography>
            </Box>
            <Box component="nav" aria-label="Navegação principal" sx={{ display: { xs: 'none', sm: 'flex' }, alignSelf: 'stretch', alignItems: 'center' }}>
              <Button component={Link} href="/atendimentos" aria-current="page" sx={{ minHeight: 76, borderRadius: 0, px: 0, borderBottom: '2px solid #254c40', color: '#254c40', '&:hover': { bgcolor: 'transparent', color: '#17382d' } }}>Atendimentos</Button>
            </Box>
            <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 2 }, minWidth: 0 }}>
              <IconButton aria-label={`Conta de ${name}`} aria-controls={anchor ? menuId : undefined} aria-haspopup="menu" aria-expanded={anchor ? 'true' : undefined} onClick={event => setAnchor(event.currentTarget)} sx={{ p: .5, gap: .6, borderRadius: 2 }}>
                <Avatar sx={{ width: 34, height: 34, bgcolor: '#e8eddc', color: '#35523d', fontSize: 14, fontWeight: 650 }}>{initial}</Avatar>
                <Box component="span" sx={{ display: { xs: 'none', sm: 'flex' } }}><ChevronDown size={14} aria-hidden="true" /></Box>
              </IconButton>
            </Box>
          </Box>
        </Box>
        <Box component="main" id="conteudo-atendimento" tabIndex={-1} sx={{ maxWidth: 1280, mx: 'auto', px: { xs: 2.5, md: 5 }, pt: { xs: 3, md: 5 }, pb: 6, outline: 'none' }}>
          {children}
        </Box>
        <Box component="footer" sx={{ maxWidth: 1280, mx: 'auto', px: { xs: 2.5, md: 5 }, pb: 3 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" gap={2} sx={{ pt: 2.5, borderTop: '1px solid', borderColor: 'divider' }}>
            <Typography variant="caption" color="text.secondary">Feito para cuidar de cada detalhe.</Typography>
            <Stack direction="row" alignItems="center" gap={.75} sx={{ flexShrink: 0 }}>
              <Box aria-hidden="true" sx={{ width: 5, height: 5, borderRadius: '50%', bgcolor: '#72916b' }} />
              <Typography variant="caption" color="text.secondary">Revisão manual</Typography>
            </Stack>
          </Stack>
        </Box>
        <Menu id={menuId} anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }} transformOrigin={{ vertical: 'top', horizontal: 'right' }}>
          <Box sx={{ px: 2, py: 1, maxWidth: 280 }}>
            <Typography variant="body2" fontWeight={650} sx={{ overflowWrap: 'anywhere' }}>{name}</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{user?.email}</Typography>
          </Box>
          <Divider sx={{ my: 1 }} />
          <MenuItem disabled={logout.isPending} onClick={() => { logout.mutate(); setAnchor(null) }} sx={{ mx: .75, borderRadius: 1.5 }}>
            <ListItemIcon><LogOut size={17} /></ListItemIcon>
            {logout.isPending ? 'Saindo…' : 'Sair da conta'}
          </MenuItem>
        </Menu>
      </Box>
    </ProtectedRoute>
  </ThemeProvider>
}
