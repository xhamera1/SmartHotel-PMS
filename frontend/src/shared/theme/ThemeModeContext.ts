import { createContext } from 'react'
import type { ThemeMode } from '@/shared/theme/themeModeStore'

export type ThemeModeContextValue = {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  toggleMode: () => void
}

export const ThemeModeContext = createContext<ThemeModeContextValue | null>(null)
