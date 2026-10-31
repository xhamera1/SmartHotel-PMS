import { test, expect } from '@playwright/test'
import { stayWindow } from '../helpers/dates'
import { uniqueEmail } from '../helpers/api'
import { confirmBooking, fillGuestAndPay, searchStay, selectFirstFlexRate } from '../helpers/booking'

test.describe('E2E-01 guest books a room @smoke', () => {
  test('search → checkout → confirmation; admin sees reservation', async ({ page }) => {
    const { checkIn, checkOut } = stayWindow(36, 2)
    const email = uniqueEmail('01', test.info().workerIndex)
    const guest = { firstName: 'E2E', lastName: 'Booker', email }

    await searchStay(page, checkIn, checkOut)
    await selectFirstFlexRate(page, 'STD')
    await fillGuestAndPay(page, guest)
    const code = await confirmBooking(page)

    await page.goto('/admin/reservations')
    await expect(page.getByTestId('admin-reservations')).toBeVisible()
    await expect(page.getByTestId(`reservation-row-${code}`)).toBeVisible()
  })
})
