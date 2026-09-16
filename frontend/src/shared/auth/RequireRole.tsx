import { useSyncExternalStore } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import type { StaffRole } from '@/shared/auth/session'
import { authSession } from '@/shared/auth/session'

type RequireRoleProps = {
  roles: StaffRole[]
}

export function RequireRole({ roles }: RequireRoleProps) {
  const role = useSyncExternalStore(authSession.subscribe, authSession.getRole, () => null)
  if (!role || !roles.includes(role)) {
    return <Navigate to="/admin" replace />
  }
  return <Outlet />
}
