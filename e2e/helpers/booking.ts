import type { Page } from '@playwright/test'
import { expect } from '@playwright/test'
import { muiInput } from './mui'

export async function searchStay(
  page: Page,
  checkIn: string,
  checkOut: string,
  guests = 2,
): Promise<void> {
  await page.goto('/booking')
  await muiInput(page, 'search-check-in').fill(checkIn)
  await muiInput(page, 'search-check-out').fill(checkOut)
  await page.getByTestId('search-guests').getByRole('combobox').click()
  await page.getByRole('option', { name: String(guests) }).click()
  await page.getByTestId('search-submit').click()
}

export async function selectFirstFlexRate(page: Page, roomTypeCode = 'STD'): Promise<void> {
  const card = page.getByTestId(`room-type-card-${roomTypeCode}`)
  await expect(card).toBeVisible()
  const flex = page.getByTestId(`select-rate-${roomTypeCode}-FLEX`)
  if (await flex.count()) {
    await flex.click()
    return
  }
  await card.getByRole('button').first().click()
}

export async function fillGuestAndPay(
  page: Page,
  guest: { firstName: string; lastName: string; email: string },
): Promise<void> {
  await expect(page.getByTestId('guest-details-form')).toBeVisible()
  await muiInput(page, 'guest-first-name').fill(guest.firstName)
  await muiInput(page, 'guest-last-name').fill(guest.lastName)
  await muiInput(page, 'guest-email').fill(guest.email)
  await page.getByTestId('mock-payment-authorize').check()
}

export async function confirmBooking(page: Page): Promise<string> {
  await page.getByTestId('confirm-booking').click()
  const code = page.getByTestId('confirmation-code')
  await expect(code).toBeVisible()
  return (await code.innerText()).trim()
}
