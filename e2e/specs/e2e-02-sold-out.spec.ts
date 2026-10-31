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
import { searchStay } from '../helpers/booking'

test.describe('E2E-02 sold-out dates', () => {
  test('pre-seeded full occupancy shows no availability', async ({ page }) => {
    const worker = test.info().workerIndex
    const code = uniqueCode('E2S', worker)
    const { checkIn, checkOut } = stayWindow(40 + worker, 1)
    const token = (await login()).accessToken
    const rt = await createRoomType(token, code)
    await createRoom(token, rt.id, uniqueRoomNumber(worker))
    await createPublicReservation({
      roomTypeCode: code,
      checkIn,
      checkOut,
      guest: {
        email: uniqueEmail('sold', worker),
        firstName: 'Full',
        lastName: 'House',
      },
    })

    await searchStay(page, checkIn, checkOut)
    await expect(page.getByTestId(`room-type-card-${code}`)).toHaveCount(0)
    await expect(page.getByTestId('availability-empty').or(page.getByTestId('availability-results'))).toBeVisible()
  })
})
