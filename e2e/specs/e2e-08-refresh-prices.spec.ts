import { test, expect } from '@playwright/test'
import { monthOf, stayWindow } from '../helpers/dates'
import { searchStay, selectFirstFlexRate } from '../helpers/booking'

test.describe('E2E-08 refresh prices updates calendar', () => {
  test('refresh then guest can still book', async ({ page }) => {
    const { checkIn, checkOut } = stayWindow(52, 2)

    await page.goto('/admin/rate-calendar')
    await page.getByTestId('rate-calendar-room-type').getByRole('combobox').click()
    await page.getByRole('option', { name: 'STD', exact: true }).click()
    await page.getByTestId('rate-calendar-month').locator('input').fill(monthOf(checkIn))
    const refresh = page.waitForResponse(
      (res) => res.url().includes('/api/v1/admin/pricing/refresh') && res.ok(),
      { timeout: 90_000 },
    )
    await page.getByTestId('refresh-prices').click()
    await refresh
    await expect(page.getByTestId('refresh-prices-message')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByTestId(`rate-cell-${checkIn}`)).toBeVisible()

    await searchStay(page, checkIn, checkOut)
    await selectFirstFlexRate(page, 'STD')
    await expect(page.getByTestId('checkout-selection')).toBeVisible()
  })
})
