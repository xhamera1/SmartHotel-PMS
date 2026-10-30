import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SearchForm } from '@/features/booking/components/SearchForm'
import { I18nProvider } from '@/shared/i18n/I18nProvider'
import { addHotelDays, todayHotelDate } from '@/shared/lib/hotelDates'

function renderForm(onSubmit = vi.fn()) {
  return render(
    <I18nProvider>
      <SearchForm onSubmit={onSubmit} />
    </I18nProvider>,
  )
}

describe('SearchForm', () => {
  afterEach(() => {
    cleanup()
  })

  it('submits valid stay dates', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderForm(onSubmit)
    const checkIn = todayHotelDate()
    const checkOut = addHotelDays(checkIn, 2)

    await user.clear(screen.getByTestId('search-check-in').querySelector('input')!)
    await user.type(screen.getByTestId('search-check-in').querySelector('input')!, checkIn)
    await user.clear(screen.getByTestId('search-check-out').querySelector('input')!)
    await user.type(screen.getByTestId('search-check-out').querySelector('input')!, checkOut)

    await user.click(screen.getByRole('button', { name: /szukaj|search/i }))
    await waitFor(() => expect(onSubmit).toHaveBeenCalled())
    expect(onSubmit.mock.calls[0]![0]).toMatchObject({ checkIn, checkOut, guests: 2 })
  })

  it('shows validation when check-out is not after check-in', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderForm(onSubmit)
    const day = todayHotelDate()

    await user.clear(screen.getByTestId('search-check-in').querySelector('input')!)
    await user.type(screen.getByTestId('search-check-in').querySelector('input')!, day)
    await user.clear(screen.getByTestId('search-check-out').querySelector('input')!)
    await user.type(screen.getByTestId('search-check-out').querySelector('input')!, day)

    await user.click(screen.getByRole('button', { name: /szukaj|search/i }))
    await waitFor(() => expect(onSubmit).not.toHaveBeenCalled())
    expect(screen.getByTestId('booking-search-form')).toBeInTheDocument()
  })
})
