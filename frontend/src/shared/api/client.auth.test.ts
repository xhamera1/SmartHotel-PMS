import { http, HttpResponse } from 'msw'
import { afterEach, describe, expect, it } from 'vitest'
import { apiClient } from '@/shared/api/client'
import { authSession } from '@/shared/auth/session'
import { server } from '@/test/msw/server'

describe('apiClient auth interceptor', () => {
  afterEach(() => {
    authSession.clear()
  })

  it('on 401 refreshes via cookie and retries the original request', async () => {
    authSession.setSession({
      accessToken: 'stale-token',
      role: 'ADMIN',
      email: 'admin@smarthotel.local',
      fullName: 'Admin',
    })

    let protectedHits = 0
    let seenAuth: string | null = null

    server.use(
      http.get('*/api/v1/admin/dashboard/kpis', ({ request }) => {
        protectedHits += 1
        const auth = request.headers.get('Authorization')
        if (auth === 'Bearer stale-token') {
          return HttpResponse.json(
            {
              type: 'https://smarthotel/problems/unauthorized',
              title: 'Unauthorized',
              status: 401,
            },
            { status: 401 },
          )
        }
        seenAuth = auth
        return HttpResponse.json({
          occupancyToday: 0.5,
          arrivalsToday: 2,
          departuresToday: 1,
          mtdRevenue: 1000,
        })
      }),
      http.post('*/api/v1/auth/refresh', () =>
        HttpResponse.json({
          accessToken: 'fresh-token',
          role: 'ADMIN',
          email: 'admin@smarthotel.local',
          fullName: 'Admin',
        }),
      ),
    )

    const { data } = await apiClient.get('/api/v1/admin/dashboard/kpis')

    expect(protectedHits).toBe(2)
    expect(seenAuth).toBe('Bearer fresh-token')
    expect(authSession.getAccessToken()).toBe('fresh-token')
    expect(data.mtdRevenue).toBe(1000)
  })

  it('rejects when refresh fails after 401', async () => {
    authSession.setSession({
      accessToken: 'stale-token',
      role: 'ADMIN',
      email: 'admin@smarthotel.local',
      fullName: 'Admin',
    })

    server.use(
      http.get('*/api/v1/admin/dashboard/kpis', () =>
        HttpResponse.json(
          {
            type: 'https://smarthotel/problems/unauthorized',
            title: 'Unauthorized',
            status: 401,
          },
          { status: 401 },
        ),
      ),
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

    await expect(apiClient.get('/api/v1/admin/dashboard/kpis')).rejects.toMatchObject({
      response: { status: 401 },
    })
    expect(authSession.getAccessToken()).toBeNull()
  })
})
