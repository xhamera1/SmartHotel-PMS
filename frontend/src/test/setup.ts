import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { authSession } from '@/shared/auth/session'
import { server } from '@/test/msw/server'

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' })
})

afterEach(() => {
  server.resetHandlers()
  authSession.clear()
})

afterAll(() => {
  server.close()
})
