import { useEffect, useMemo, useSyncExternalStore, type ReactNode } from 'react'
import { I18nContext } from '@/shared/i18n/I18nContext'
import { getMessages, interpolate, localeStore } from '@/shared/i18n/localeStore'
import type { AppLocale } from '@/shared/i18n/messages'

export function I18nProvider({ children }: { children: ReactNode }) {
  const current = useSyncExternalStore(
    localeStore.subscribe,
    localeStore.get,
    () => 'pl' as AppLocale,
  )
  const value = useMemo(
    () => ({
      locale: current,
      setLocale: localeStore.set,
      t: getMessages(current),
      tf: interpolate,
    }),
    [current],
  )

  useEffect(() => {
    document.documentElement.lang = current
    document.title = getMessages(current).documentTitle
  }, [current])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
