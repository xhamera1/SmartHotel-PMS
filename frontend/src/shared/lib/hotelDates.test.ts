import { describe, expect, it } from 'vitest'
import {
  addHotelDays,
  formatHotelDate,
  formatHotelDateDisplay,
  isHotelDate,
  nightsBetween,
  parseHotelDate,
} from '@/shared/lib/hotelDates'

describe('hotelDates', () => {
  it('parses and formats without UTC midnight shift', () => {
    const parsed = parseHotelDate('2026-10-01')
    expect(formatHotelDate(parsed)).toBe('2026-10-01')
    expect(formatHotelDateDisplay('2026-10-01')).toMatch(/2026/)
  })

  it('validates ISO hotel dates', () => {
    expect(isHotelDate('2026-02-28')).toBe(true)
    expect(isHotelDate('2026-02-30')).toBe(false)
    expect(isHotelDate('2026-2-01')).toBe(false)
  })

  it('computes nights and addHotelDays', () => {
    expect(nightsBetween('2026-10-01', '2026-10-04')).toBe(3)
    expect(addHotelDays('2026-10-01', 2)).toBe('2026-10-03')
  })
})
