import { Box, Button, Container, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import { apiClient } from '@/shared/api/client'
import type { components } from '@/shared/api/schema'
import { authSession } from '@/shared/auth/session'
import { useI18n } from '@/shared/i18n/useI18n'
import { AppChromeControls } from '@/shared/ui/AppChromeControls'
import { MainContent } from '@/shared/ui/MainContent'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'
import { SkipToContent } from '@/shared/ui/SkipToContent'

type TokenResponse = components['schemas']['TokenResponse']

export function AdminLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useI18n()
  const from = (location.state as { from?: string } | null)?.from ?? '/admin'
  const [email, setEmail] = useState('admin@smarthotel.local')
  const [password, setPassword] = useState('admin-dev-password')
  const [error, setError] = useState<unknown>(null)
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', {
        email,
        password,
      })
      if (!data.accessToken || !data.role || !data.email || !data.fullName) {
        throw new Error(t.admin.incompleteToken)
      }
      authSession.setSession({
        accessToken: data.accessToken,
        role: data.role,
        email: data.email,
        fullName: data.fullName,
      })
      void navigate(from, { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setPending(false)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <SkipToContent />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 2,
          flexWrap: 'wrap',
          mb: 2,
        }}
      >
        <Typography
          variant="h6"
          component={RouterLink}
          to="/"
          sx={{
            textDecoration: 'none',
            color: 'primary.main',
            fontFamily: 'Fraunces, serif',
          }}
          data-testid="admin-login-home"
        >
          {t.hotelName}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          <AppChromeControls />
        </Box>
      </Box>
      <MainContent>
        <Typography variant="h4" component="h1" gutterBottom>
          {t.admin.loginTitle}
        </Typography>
        <Box
          component="form"
          onSubmit={onSubmit}
          noValidate
          data-testid="admin-login-form"
          sx={{ display: 'grid', gap: 2 }}
        >
          <TextField
            label={t.common.email}
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            data-testid="admin-login-email"
          />
          <TextField
            label={t.common.password}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            data-testid="admin-login-password"
          />
          {error ? (
            <ProblemAlert
              error={error}
              fallback={t.admin.loginFailed}
              data-testid="admin-login-error"
            />
          ) : null}
          <Button
            type="submit"
            variant="contained"
            disabled={pending}
            data-testid="admin-login-submit"
          >
            {pending ? t.admin.signingIn : t.admin.signIn}
          </Button>
          <Button component={RouterLink} to="/" variant="text" data-testid="admin-login-back-home">
            {t.booking.home}
          </Button>
        </Box>
      </MainContent>
    </Container>
  )
}
