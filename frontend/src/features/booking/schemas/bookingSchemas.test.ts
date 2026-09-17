import { describe, expect, it } from 'vitest'
import {
  MAX_STAY_NIGHTS,
  guestDetailsSchema,
  manageLookupSchema,
  searchStaySchema,
} from '@/features/booking/schemas/bookingSchemas'
import { addHotelDays, todayHotelDate } from '@/shared/lib/hotelDates'

describe('searchStaySchema', () => {
  it('accepts a valid short stay from today', () => {
    const checkIn = todayHotelDate()
    const checkOut = addHotelDays(checkIn, 2)
    const parsed = searchStaySchema.safeParse({ checkIn, checkOut, guests: 2 })
    expect(parsed.success).toBe(true)
  })

  it('rejects checkout on or before check-in', () => {
    const checkIn = todayHotelDate()
    const parsed = searchStaySchema.safeParse({
      checkIn,
      checkOut: checkIn,
      guests: 1,
    })
    expect(parsed.success).toBe(false)
    if (!parsed.success) {
      expect(parsed.error.issues.some((i) => i.path.includes('checkOut'))).toBe(true)
    }
  })

  it('rejects stays longer than max nights', () => {
    const checkIn = todayHotelDate()
    const parsed = searchStaySchema.safeParse({
      checkIn,
      checkOut: addHotelDays(checkIn, MAX_STAY_NIGHTS + 1),
      guests: 2,
    })
    expect(parsed.success).toBe(false)
  })

  it('rejects guest counts outside 1–10', () => {
    const checkIn = todayHotelDate()
    const checkOut = addHotelDays(checkIn, 1)
    expect(searchStaySchema.safeParse({ checkIn, checkOut, guests: 0 }).success).toBe(false)
    expect(searchStaySchema.safeParse({ checkIn, checkOut, guests: 11 }).success).toBe(false)
  })
})

describe('guestDetailsSchema', () => {
  it('requires payment authorization', () => {
    const parsed = guestDetailsSchema.safeParse({
      firstName: 'Jan',
      lastName: 'Kowalski',
      email: 'jan@example.com',
      phone: '',
      paymentAuthorized: false,
    })
    expect(parsed.success).toBe(false)
  })

  it('accepts a complete guest + mock payment', () => {
    const parsed = guestDetailsSchema.safeParse({
      firstName: 'Jan',
      lastName: 'Kowalski',
      email: 'jan@example.com',
      phone: '+48 600 100 200',
      paymentAuthorized: true,
    })
    expect(parsed.success).toBe(true)
  })
})

describe('manageLookupSchema', () => {
  it('uppercases confirmation codes', () => {
    const parsed = manageLookupSchema.parse({
      code: 'ab12cd34',
      email: 'guest@example.com',
    })
    expect(parsed.code).toBe('AB12CD34')
  })
})
