import { Alert, Box, Button, Container, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { apiClient } from '@/shared/api/client'
import type { components } from '@/shared/api/schema'
import { authSession } from '@/shared/auth/session'

type TokenResponse = components['schemas']['TokenResponse']

export function AdminLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/admin'
  const [email, setEmail] = useState('admin@smarthotel.local')
  const [password, setPassword] = useState('admin-dev-password')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', { email, password })
      if (!data.accessToken || !data.role || !data.email || !data.fullName) {
        throw new Error('Incomplete token response')
      }
      authSession.setSession({
        accessToken: data.accessToken,
        role: data.role,
        email: data.email,
        fullName: data.fullName,
      })
      void navigate(from, { replace: true })
    } catch {
      setError('Login failed — check email and password.')
    } finally {
      setPending(false)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Staff login
      </Typography>
      <Box component="form" onSubmit={onSubmit} sx={{ display: 'grid', gap: 2 }}>
        <TextField
          label="Email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error ? <Alert severity="error">{error}</Alert> : null}
        <Button type="submit" variant="contained" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </Button>
      </Box>
    </Container>
  )
}
