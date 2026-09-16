import { AppBar, Box, Button, Container, Toolbar, Typography } from '@mui/material'
import { useSyncExternalStore } from 'react'
import { Link as RouterLink, Outlet, useNavigate } from 'react-router-dom'
import { logoutSession } from '@/shared/api/client'
import { authSession } from '@/shared/auth/session'

export function AdminShell() {
  const navigate = useNavigate()
  const role = useSyncExternalStore(authSession.subscribe, authSession.getRole, () => null)
  const name = useSyncExternalStore(authSession.subscribe, authSession.getFullName, () => null)

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" color="primary" elevation={0}>
        <Toolbar sx={{ gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SmartHotel Admin
          </Typography>
          <Button color="inherit" component={RouterLink} to="/admin">
            Dashboard
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin/reservations">
            Reservations
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin/guests">
            Guests
          </Button>
          {role === 'ADMIN' ? (
            <>
              <Button color="inherit" component={RouterLink} to="/admin/room-types">
                Room types
              </Button>
              <Button color="inherit" component={RouterLink} to="/admin/rooms">
                Rooms
              </Button>
              <Button color="inherit" component={RouterLink} to="/admin/rate-calendar">
                Rates
              </Button>
            </>
          ) : null}
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            {name} ({role})
          </Typography>
          <Button
            color="inherit"
            onClick={() => {
              void logoutSession().then(() => navigate('/admin/login', { replace: true }))
            }}
          >
            Log out
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Outlet />
      </Container>
    </Box>
  )
}
