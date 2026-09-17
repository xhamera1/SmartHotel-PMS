import { createContext } from 'react'
import type { AppLocale, Messages } from '@/shared/i18n/messages'

export type I18nContextValue = {
  locale: AppLocale
  setLocale: (locale: AppLocale) => void
  t: Messages
  tf: (template: string, vars: Record<string, string | number>) => string
}

export const I18nContext = createContext<I18nContextValue | null>(null)
