import { CssBaseline } from '@mui/material'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { router } from '@/app/router'
import { I18nProvider } from '@/shared/i18n/I18nProvider'
import { queryClient } from '@/shared/api/queryClient'
import { AppThemeProvider } from '@/shared/theme/ThemeModeProvider'
import { AppErrorBoundary } from '@/shared/ui/AppErrorBoundary'

export function App() {
  return (
    <I18nProvider>
      <AppThemeProvider>
        <AppErrorBoundary>
          <QueryClientProvider client={queryClient}>
            <CssBaseline />
            <RouterProvider router={router} />
          </QueryClientProvider>
        </AppErrorBoundary>
      </AppThemeProvider>
    </I18nProvider>
  )
}
