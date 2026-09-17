export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'wpr-theme-mode'

type ModeListener = () => void

let mode: ThemeMode = readStoredMode()
const listeners = new Set<ModeListener>()

function readStoredMode(): ThemeMode {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === 'dark' || raw === 'light') {
      return raw
    }
  } catch {
    // ignore
  }
  return 'light'
}

function notify() {
  listeners.forEach((listener) => listener())
}

export const themeModeStore = {
  get: () => mode,
  set(next: ThemeMode) {
    mode = next
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // ignore
    }
    notify()
  },
  toggle() {
    themeModeStore.set(mode === 'light' ? 'dark' : 'light')
  },
  subscribe(listener: ModeListener) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}
