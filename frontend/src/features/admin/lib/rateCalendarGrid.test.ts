import { describe, expect, it } from 'vitest'
import type { RateCalendarDay } from '@/features/admin/api/adminApi'
import { rateSourceLabel } from '@/features/admin/lib/rateSource'

/** Mirrors RateCalendarPage cell mapping: date → day → source badge label. */
function cellSourceLabel(days: RateCalendarDay[], iso: string): string {
  const day = days.find((d) => d.date === iso)
  return rateSourceLabel(day?.source)
}

describe('rate calendar grid cell sources', () => {
  const days: RateCalendarDay[] = [
    { date: '2027-06-14', price: 300, source: 'ML_MODEL', demandIndicator: 40 },
    { date: '2027-06-15', price: 280, source: 'MANUAL', demandIndicator: 10 },
    { date: '2027-06-16', price: 250, source: 'BASE_FALLBACK', demandIndicator: 0 },
  ]

  it('maps ML / MANUAL / FALLBACK labels for grid cells', () => {
    expect(cellSourceLabel(days, '2027-06-14')).toBe('ML')
    expect(cellSourceLabel(days, '2027-06-15')).toBe('MANUAL')
    expect(cellSourceLabel(days, '2027-06-16')).toBe('FALLBACK')
  })

  it('defaults missing calendar days to BASE', () => {
    expect(cellSourceLabel(days, '2027-06-17')).toBe('BASE')
  })
})
