import { Box, CircularProgress } from '@mui/material'
import { useEffect, useState, useSyncExternalStore } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { refreshAccessToken } from '@/shared/api/client'
import { authSession } from '@/shared/auth/session'

export function RequireAuth() {
  const location = useLocation()
  const authenticated = useSyncExternalStore(
    authSession.subscribe,
    authSession.isAuthenticated,
    () => false,
  )
  const [hydrating, setHydrating] = useState(!authenticated)

  useEffect(() => {
    if (authenticated) {
      return
    }
    let cancelled = false
    void refreshAccessToken().finally(() => {
      if (!cancelled) {
        setHydrating(false)
      }
    })
    return () => {
      cancelled = true
    }
  }, [authenticated])

  if (hydrating && !authenticated) {
    return (
      <Box sx={{ py: 8, display: 'grid', placeItems: 'center' }}>
        <CircularProgress aria-label="Restoring session" />
      </Box>
    )
  }

  if (!authenticated) {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}
