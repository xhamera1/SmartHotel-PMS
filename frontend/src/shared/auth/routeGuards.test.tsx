import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { RequireAuth } from '@/shared/auth/RequireAuth'
import { RequireRole } from '@/shared/auth/RequireRole'
import { authSession } from '@/shared/auth/session'
import { I18nProvider } from '@/shared/i18n/I18nProvider'
import { server } from '@/test/msw/server'

function renderGuards(initialPath: string) {
  const router = createMemoryRouter(
    [
      { path: '/admin/login', element: <div data-testid="login-page">login</div> },
      {
        path: '/admin',
        element: <RequireAuth />,
        children: [
          { index: true, element: <div data-testid="admin-home">admin home</div> },
          {
            element: <RequireRole roles={['ADMIN']} />,
            children: [
              { path: 'room-types', element: <div data-testid="room-types-page">room types</div> },
            ],
          },
        ],
      },
    ],
    { initialEntries: [initialPath] },
  )
  return render(
    <I18nProvider>
      <RouterProvider router={router} />
    </I18nProvider>,
  )
}

describe('route guards', () => {
  afterEach(() => {
    cleanup()
    authSession.clear()
  })

  it('redirects unauthenticated users to login when refresh fails', async () => {
    server.use(
      http.post('*/api/v1/auth/refresh', () =>
        HttpResponse.json(
          {
            type: 'https://smarthotel/problems/unauthorized',
            title: 'Unauthorized',
            status: 401,
          },
          { status: 401 },
        ),
      ),
    )

    renderGuards('/admin')

    expect(await screen.findByTestId('login-page')).toBeInTheDocument()
  })

  it('allows access after silent refresh restores the session', async () => {
    renderGuards('/admin')

    expect(await screen.findByTestId('admin-home')).toBeInTheDocument()
    expect(authSession.getAccessToken()).toBe('access-refreshed')
  })

  it('allows authenticated ADMIN into ADMIN-only routes', async () => {
    authSession.setSession({
      accessToken: 'tok',
      role: 'ADMIN',
      email: 'admin@smarthotel.local',
      fullName: 'Admin',
    })

    renderGuards('/admin/room-types')

    expect(await screen.findByTestId('room-types-page')).toBeInTheDocument()
  })

  it('redirects RECEPTIONIST away from ADMIN-only routes', async () => {
    authSession.setSession({
      accessToken: 'tok',
      role: 'RECEPTIONIST',
      email: 'recept@smarthotel.local',
      fullName: 'Reception',
    })

    renderGuards('/admin/room-types')

    await waitFor(() => {
      expect(screen.getByTestId('admin-home')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('room-types-page')).not.toBeInTheDocument()
  })
})
