import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from '@/app/App'

async function enableMocking() {
  if (import.meta.env.VITE_MSW !== 'true') {
    return
  }
  const { worker } = await import('@/test/msw/browser')
  return worker.start({ onUnhandledRequest: 'bypass' })
}

const root = document.getElementById('root')
if (!root) {
  throw new Error('Root element #root not found')
}

enableMocking().then(() => {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
