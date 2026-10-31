import { test, expect } from '@playwright/test'
import { stayWindow } from '../helpers/dates'
import { createRoom, createRoomType, login, uniqueCode, uniqueRoomNumber } from '../helpers/api'
import { searchStay } from '../helpers/booking'

test.describe('E2E-05 admin room-type CRUD reflected in search', () => {
  test('new room type appears in public availability', async ({ page }) => {
    const worker = test.info().workerIndex
    const code = uniqueCode('E2T', worker)
    const { checkIn, checkOut } = stayWindow(44 + worker, 2)
    const token = (await login()).accessToken
    const rt = await createRoomType(token, code, { capacity: 2, basePrice: 310 })
    await createRoom(token, rt.id, uniqueRoomNumber(worker))

    const availability = page.waitForResponse(
      (res) =>
        res.url().includes('/api/v1/availability') &&
        res.request().method() === 'GET' &&
        res.ok(),
      { timeout: 30_000 },
    )
    await searchStay(page, checkIn, checkOut)
    await availability
    await expect(page.getByTestId(`room-type-card-${code}`)).toBeVisible({ timeout: 30_000 })
  })
})
