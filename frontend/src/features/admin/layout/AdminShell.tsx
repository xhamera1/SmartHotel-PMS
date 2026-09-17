import { AppBar, Box, Button, Container, Toolbar, Typography } from '@mui/material'
import { useSyncExternalStore } from 'react'
import { Link as RouterLink, Outlet, useNavigate } from 'react-router-dom'
import { logoutSession } from '@/shared/api/client'
import { authSession } from '@/shared/auth/session'
import { useI18n } from '@/shared/i18n/useI18n'
import { AppChromeControls } from '@/shared/ui/AppChromeControls'
import { MainContent } from '@/shared/ui/MainContent'
import { SkipToContent } from '@/shared/ui/SkipToContent'

export function AdminShell() {
  const navigate = useNavigate()
  const { t } = useI18n()
  const role = useSyncExternalStore(authSession.subscribe, authSession.getRole, () => null)
  const name = useSyncExternalStore(authSession.subscribe, authSession.getFullName, () => null)

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <SkipToContent />
      <AppBar position="sticky" color="primary" elevation={0} component="header">
        <Toolbar sx={{ gap: 1.5, flexWrap: 'wrap' }} component="nav" aria-label={t.nav.adminAria}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {t.nav.adminBrand}
          </Typography>
          <Button color="inherit" component={RouterLink} to="/admin">
            {t.nav.dashboard}
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin/reservations">
            {t.nav.reservations}
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin/guests">
            {t.nav.guests}
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin/rate-calendar">
            {t.nav.rates}
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin/events">
            {t.nav.events}
          </Button>
          {role === 'ADMIN' ? (
            <>
              <Button color="inherit" component={RouterLink} to="/admin/room-types">
                {t.nav.roomTypes}
              </Button>
              <Button color="inherit" component={RouterLink} to="/admin/rooms">
                {t.nav.rooms}
              </Button>
            </>
          ) : null}
          <AppChromeControls tone="inherit" />
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            {name} ({role})
          </Typography>
          <Button
            color="inherit"
            onClick={() => {
              void logoutSession().then(() => navigate('/admin/login', { replace: true }))
            }}
            data-testid="admin-logout"
          >
            {t.nav.logOut}
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <MainContent>
          <Outlet />
        </MainContent>
      </Container>
    </Box>
  )
}
