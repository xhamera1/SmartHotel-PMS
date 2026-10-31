import { defineConfig, devices } from '@playwright/test'

// Use localhost (not 127.0.0.1) so Origin matches CORS_ALLOWED_ORIGINS in compose.
const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:8088'

export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 1,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  outputDir: 'test-results',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL,
    locale: 'pl-PL',
    timezoneId: 'Europe/Warsaw',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup'],
      testIgnore: [/e2e-10/, /auth\.setup\.ts/],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup'],
      testIgnore: [/e2e-10/, /auth\.setup\.ts/],
    },
    {
      name: 'fault',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/admin.json',
      },
      // After chromium: E2E-10 stops pricing and must not race refresh/book specs.
      dependencies: ['chromium'],
      testMatch: /e2e-10/,
      fullyParallel: false,
      workers: 1,
    },
  ],
})
