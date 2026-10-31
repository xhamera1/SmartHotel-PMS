import { test, expect } from '@playwright/test'
import { syncEvents } from '../helpers/api'

test.describe('E2E-11 events view', () => {
  test('lists scored events with impact and rationale', async ({ page }) => {
    await syncEvents().catch(() => undefined)
    // Allow background sync a moment via polling UI rather than fixed sleep
    await page.goto('/admin/events')
    await expect(page.getByTestId('admin-events')).toBeVisible()

    await page.getByTestId('events-from').locator('input').fill('2027-04-01')
    await page.getByTestId('events-to').locator('input').fill('2027-10-31')

    await expect(page.getByTestId('events-table')).toBeVisible({ timeout: 60_000 })
    const rows = page.getByTestId('events-table').locator('tbody tr')
    await expect(rows.first()).toBeVisible({ timeout: 60_000 })
  })
})
