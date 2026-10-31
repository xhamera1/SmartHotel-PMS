import { test, expect } from '@playwright/test'

test.describe('E2E-09 auth role matrix', () => {
  test('anonymous is redirected to login', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    await page.goto('/admin/reservations')
    await expect(page).toHaveURL(/\/admin\/login/)
    await expect(page.getByTestId('admin-login-form')).toBeVisible()
    await context.close()
  })

  test('receptionist cannot open room-types settings', async ({ browser }) => {
    const context = await browser.newContext({ storageState: '.auth/reception.json' })
    const page = await context.newPage()
    await page.goto('/admin/room-types')
    await expect(page.getByTestId('admin-room-types')).toHaveCount(0)
    await expect(page).toHaveURL(/\/admin\/?$/)
    await expect(page.getByTestId('admin-dashboard')).toBeVisible()
    await context.close()
  })
})
