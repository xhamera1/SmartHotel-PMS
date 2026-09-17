import { type AppLocale, type Messages, messagesByLocale } from '@/shared/i18n/messages'

const STORAGE_KEY = 'wpr-locale'

type LocaleListener = () => void

let locale: AppLocale = readStoredLocale()
const listeners = new Set<LocaleListener>()

function readStoredLocale(): AppLocale {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === 'en' || raw === 'pl') {
      return raw
    }
  } catch {
    // ignore
  }
  return 'pl'
}

function notify() {
  listeners.forEach((listener) => listener())
}

export const localeStore = {
  get: () => locale,
  set(next: AppLocale) {
    locale = next
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // ignore
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = next
      document.title = messagesByLocale[next].documentTitle
    }
    notify()
  },
  subscribe(listener: LocaleListener) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}

export function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(vars[key] ?? ''))
}

export function getMessages(current: AppLocale = localeStore.get()): Messages {
  return messagesByLocale[current]
}
