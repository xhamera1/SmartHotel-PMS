import { test, expect } from '@playwright/test'
import { addDaysIso, todayIso } from '../helpers/dates'
import { createAdminReservation, login, uniqueEmail } from '../helpers/api'

test.describe('E2E-06 reservation lifecycle', () => {
  test('check-in → check-out; illegal actions gone', async ({ page }) => {
    const worker = test.info().workerIndex
    const checkIn = todayIso()
    const checkOut = addDaysIso(checkIn, 1)
    const token = (await login()).accessToken
    const reservation = await createAdminReservation(token, {
      roomTypeCode: 'STD',
      checkIn,
      checkOut,
      guest: {
        email: uniqueEmail('06', worker),
        firstName: 'Life',
        lastName: 'Cycle',
      },
    })

    await page.goto('/admin/reservations')
    await page.getByTestId(`reservation-row-${reservation.confirmationCode}`).click()
    await expect(page.getByTestId('reservation-drawer')).toBeVisible()
    await expect(page.getByTestId('reservation-action-check-in')).toBeVisible()
    await page.getByTestId('reservation-action-check-in').click()
    await expect(page.getByTestId('reservation-action-check-out')).toBeVisible()
    await expect(page.getByTestId('reservation-action-check-in')).toHaveCount(0)
    await page.getByTestId('reservation-action-check-out').click()
    await expect(page.getByTestId('reservation-action-check-out')).toHaveCount(0)
    await expect(page.getByTestId('reservation-action-cancel')).toHaveCount(0)
  })
})
