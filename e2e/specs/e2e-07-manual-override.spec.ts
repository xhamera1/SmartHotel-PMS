import { test, expect } from '@playwright/test'
import { monthOf, stayWindow } from '../helpers/dates'
import { login, putManualRate, refreshPrices } from '../helpers/api'

test.describe('E2E-07 manual override survives refresh @smoke', () => {
  test('MANUAL price wins over refresh', async ({ page }) => {
    const { checkIn } = stayWindow(50, 1)
    const token = (await login()).accessToken
    const overridePrice = 420
    await putManualRate(token, 'STD', checkIn, overridePrice)
    await refreshPrices(token)

    await page.goto('/admin/rate-calendar')
    await expect(page.getByTestId('admin-rate-calendar')).toBeVisible()
    await page.getByTestId('rate-calendar-room-type').getByRole('combobox').click()
    await page.getByRole('option', { name: 'STD', exact: true }).click()
    await page.getByTestId('rate-calendar-month').locator('input').fill(monthOf(checkIn))
    const cell = page.getByTestId(`rate-cell-${checkIn}`)
    await expect(cell).toBeVisible()
    await expect(cell).toContainText(String(overridePrice))
    await expect(cell).toContainText('MANUAL')
  })
})
