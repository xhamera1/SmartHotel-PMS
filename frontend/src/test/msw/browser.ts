import { setupWorker } from 'msw/browser'
import { handlers } from '@/test/msw/handlers'

/**
 * Browser MSW worker for dev mode — reuses the same handlers as tests.
 * Start with: VITE_MSW=true pnpm dev
 */
export const worker = setupWorker(...handlers)
