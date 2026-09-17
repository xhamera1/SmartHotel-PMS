import { setupServer } from 'msw/node'
import { handlers } from '@/test/msw/handlers'

/** Shared MSW server — Vitest setup + future Vite mock mode. */
export const server = setupServer(...handlers)
