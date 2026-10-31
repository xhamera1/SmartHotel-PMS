import { test, expect } from '@playwright/test'
import { stayWindow } from '../helpers/dates'
import { uniqueEmail } from '../helpers/api'
import { confirmBooking, fillGuestAndPay, searchStay, selectFirstFlexRate } from '../helpers/booking'
import { startPricing, stopPricing } from '../helpers/docker'

test.describe('E2E-10 pricing down fallback @smoke @fault', () => {
  test.afterEach(async () => {
    await startPricing().catch(() => undefined)
  })

  test('booking completes at base rate; admin sees fallback banner', async ({ page }) => {
    await stopPricing()
    const { checkIn, checkOut } = stayWindow(55, 2)
    const email = uniqueEmail('10', test.info().workerIndex)

    await searchStay(page, checkIn, checkOut)
    await selectFirstFlexRate(page, 'STD')
    await fillGuestAndPay(page, { firstName: 'Fallback', lastName: 'Guest', email })
    await confirmBooking(page)

    await page.goto('/admin/rate-calendar')
    await expect(page.getByTestId('admin-rate-calendar')).toBeVisible()
    const refreshResponse = page.waitForResponse(
      (res) => res.url().includes('/api/v1/admin/pricing/refresh'),
      { timeout: 60_000 },
    )
    await page.getByTestId('refresh-prices').click()
    await refreshResponse
    await expect(page.getByTestId('pricing-fallback-banner')).toBeVisible({ timeout: 30_000 })
  })
})
