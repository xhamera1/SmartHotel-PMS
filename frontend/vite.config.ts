/// <reference types="vitest/config" />
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, '')
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(rootDir, 'src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
      css: false,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'lcov'],
        include: [
          'src/shared/api/**/*.{ts,tsx}',
          'src/shared/auth/**/*.{ts,tsx}',
          'src/shared/lib/**/*.{ts,tsx}',
          'src/features/booking/schemas/**/*.ts',
          'src/features/admin/lib/rateSource.ts',
          'src/features/admin/components/RateSourceBadge.tsx',
        ],
        exclude: ['src/shared/api/schema.d.ts', 'src/**/*.test.{ts,tsx}', 'src/test/**'],
        thresholds: {
          lines: 60,
          functions: 55,
          branches: 50,
          statements: 60,
        },
      },
    },
  }
})
