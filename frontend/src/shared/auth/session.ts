import type { components } from '@/shared/api/schema'

export type StaffRole = NonNullable<components['schemas']['TokenResponse']['role']>

type SessionListener = () => void

/**
 * Access token + staff profile live in module memory only.
 * Refresh JWT is an httpOnly cookie set by the backend (ADR-0014) — never readable here.
 */
let accessToken: string | null = null
let role: StaffRole | null = null
let email: string | null = null
let fullName: string | null = null

const listeners = new Set<SessionListener>()

function notify() {
  listeners.forEach((listener) => listener())
}

export const authSession = {
  getAccessToken: () => accessToken,
  getRole: () => role,
  getEmail: () => email,
  getFullName: () => fullName,
  isAuthenticated: () => Boolean(accessToken),

  setSession(next: { accessToken: string; role: StaffRole; email: string; fullName: string }) {
    accessToken = next.accessToken
    role = next.role
    email = next.email
    fullName = next.fullName
    notify()
  },

  clear() {
    accessToken = null
    role = null
    email = null
    fullName = null
    notify()
  },

  subscribe(listener: SessionListener) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}
