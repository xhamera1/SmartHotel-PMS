/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_LOCALE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
