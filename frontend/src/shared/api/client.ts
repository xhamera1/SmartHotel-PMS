import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { authSession } from '@/shared/auth/session'
import { REQUEST_ID_HEADER, createRequestId } from '@/shared/lib/requestId'
import type { components } from '@/shared/api/schema'

type TokenResponse = components['schemas']['TokenResponse']
type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean }

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  headers: { Accept: 'application/json' },
})

let refreshPromise: Promise<boolean> | null = null

function applyAccessSession(data: TokenResponse): boolean {
  if (!data.accessToken || !data.role || !data.email || !data.fullName) {
    authSession.clear()
    return false
  }
  authSession.setSession({
    accessToken: data.accessToken,
    role: data.role,
    email: data.email,
    fullName: data.fullName,
  })
  return true
}

/** Silent refresh using the httpOnly refresh cookie (no body). Dedupes concurrent 401s. */
export async function refreshAccessToken(): Promise<boolean> {
  try {
    const { data } = await axios.post<TokenResponse>(
      `${baseURL}/api/v1/auth/refresh`,
      null,
      {
        withCredentials: true,
        headers: {
          Accept: 'application/json',
          [REQUEST_ID_HEADER]: createRequestId(),
        },
      },
    )
    return applyAccessSession(data)
  } catch {
    authSession.clear()
    return false
  }
}

export async function logoutSession(): Promise<void> {
  try {
    await axios.post(`${baseURL}/api/v1/auth/logout`, null, {
      withCredentials: true,
      headers: { [REQUEST_ID_HEADER]: createRequestId() },
    })
  } catch {
    // Cookie clear is best-effort; always drop in-memory access.
  } finally {
    authSession.clear()
  }
}

apiClient.interceptors.request.use((config) => {
  const headers = axios.AxiosHeaders.from(config.headers)
  headers.set(REQUEST_ID_HEADER, createRequestId())
  const token = authSession.getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  config.headers = headers
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined
    if (!original || error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    const url = original.url ?? ''
    if (
      url.includes('/api/v1/auth/login') ||
      url.includes('/api/v1/auth/refresh') ||
      url.includes('/api/v1/auth/logout')
    ) {
      return Promise.reject(error)
    }

    original._retry = true
    refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null
    })
    const refreshed = await refreshPromise
    if (!refreshed) {
      return Promise.reject(error)
    }

    const headers = axios.AxiosHeaders.from(original.headers)
    const token = authSession.getAccessToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    headers.set(REQUEST_ID_HEADER, createRequestId())
    original.headers = headers
    return apiClient.request(original)
  },
)
