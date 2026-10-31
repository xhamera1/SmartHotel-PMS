import { test, expect } from '@playwright/test'
import { stayWindow } from '../helpers/dates'
import { createPublicReservation, uniqueEmail } from '../helpers/api'
import { muiInput } from '../helpers/mui'

test.describe('E2E-04 guest cancel', () => {
  test('cancel via confirmation code + email', async ({ page }) => {
    const worker = test.info().workerIndex
    const { checkIn, checkOut } = stayWindow(38, 2)
    const email = uniqueEmail('04', worker)
    const reservation = await createPublicReservation({
      roomTypeCode: 'STD',
      checkIn,
      checkOut,
      guest: { email, firstName: 'Cancel', lastName: 'Me' },
    })

    await page.goto('/booking/manage')
    await muiInput(page, 'manage-code').fill(reservation.confirmationCode)
    await muiInput(page, 'manage-email').fill(email)
    await page.getByTestId('manage-lookup-submit').click()
    await expect(page.getByTestId('cancel-booking')).toBeVisible()
    await page.getByTestId('cancel-booking').click()
    await expect(page.getByTestId('cancel-confirm-dialog')).toBeVisible()
    await page.getByTestId('cancel-confirm-submit').click()
    await expect(page.getByTestId('cancel-success')).toBeVisible()
    await expect(page.getByTestId('cancel-booking')).toHaveCount(0)
  })
})
