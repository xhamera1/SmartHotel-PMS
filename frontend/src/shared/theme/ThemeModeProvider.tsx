import { useEffect, useMemo, useSyncExternalStore, type ReactNode } from 'react'
import { ThemeProvider } from '@mui/material'
import { ThemeModeContext } from '@/shared/theme/ThemeModeContext'
import { createAppTheme } from '@/shared/theme/theme'
import { themeModeStore, type ThemeMode } from '@/shared/theme/themeModeStore'

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const current = useSyncExternalStore(
    themeModeStore.subscribe,
    themeModeStore.get,
    () => 'light' as ThemeMode,
  )
  const theme = useMemo(() => createAppTheme(current), [current])
  const value = useMemo(
    () => ({
      mode: current,
      setMode: themeModeStore.set,
      toggleMode: themeModeStore.toggle,
    }),
    [current],
  )

  useEffect(() => {
    document.documentElement.dataset.colorScheme = current
  }, [current])

  return (
    <ThemeModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>{children}</ThemeProvider>
    </ThemeModeContext.Provider>
  )
}
