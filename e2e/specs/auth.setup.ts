import { test as setup, expect } from '@playwright/test'
import { ADMIN_EMAIL, ADMIN_PASSWORD, RECEPTION_EMAIL, RECEPTION_PASSWORD } from '../helpers/env'

setup('authenticate admin', async ({ page }) => {
  await page.goto('/admin/login')
  await page.getByTestId('admin-login-email').locator('input').fill(ADMIN_EMAIL)
  await page.getByTestId('admin-login-password').locator('input').fill(ADMIN_PASSWORD)
  await page.getByTestId('admin-login-submit').click()
  await expect(page.getByTestId('admin-dashboard')).toBeVisible()
  await page.context().storageState({ path: '.auth/admin.json' })
})

setup('authenticate receptionist', async ({ page }) => {
  await page.goto('/admin/login')
  await page.getByTestId('admin-login-email').locator('input').fill(RECEPTION_EMAIL)
  await page.getByTestId('admin-login-password').locator('input').fill(RECEPTION_PASSWORD)
  await page.getByTestId('admin-login-submit').click()
  await expect(page.getByTestId('admin-dashboard')).toBeVisible()
  await page.context().storageState({ path: '.auth/reception.json' })
})
