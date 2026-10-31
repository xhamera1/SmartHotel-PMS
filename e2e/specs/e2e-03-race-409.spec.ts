import { test, expect } from '@playwright/test'
import { stayWindow } from '../helpers/dates'
import {
  createPublicReservation,
  createRoom,
  createRoomType,
  login,
  uniqueCode,
  uniqueEmail,
  uniqueRoomNumber,
} from '../helpers/api'
import { fillGuestAndPay, searchStay } from '../helpers/booking'

test.describe('E2E-03 double-booking race', () => {
  test('API takes last room mid-flow → friendly 409', async ({ page }) => {
    const worker = test.info().workerIndex
    const code = uniqueCode('E2R', worker)
    const { checkIn, checkOut } = stayWindow(42 + worker, 1)
    const token = (await login()).accessToken
    const rt = await createRoomType(token, code)
    await createRoom(token, rt.id, uniqueRoomNumber(worker))

    await searchStay(page, checkIn, checkOut)
    await expect(page.getByTestId(`room-type-card-${code}`)).toBeVisible()
    await page.getByTestId(`select-rate-${code}-FLEX`).click()

    const email = uniqueEmail('race-ui', worker)
    await fillGuestAndPay(page, { firstName: 'Race', lastName: 'Guest', email })

    await createPublicReservation({
      roomTypeCode: code,
      checkIn,
      checkOut,
      guest: {
        email: uniqueEmail('race-api', worker),
        firstName: 'Api',
        lastName: 'Winner',
      },
    })

    await page.getByTestId('confirm-booking').click()
    await expect(page.getByTestId('checkout-error')).toBeVisible()
    await expect(page.getByTestId('confirmation-code')).toHaveCount(0)
  })
})
