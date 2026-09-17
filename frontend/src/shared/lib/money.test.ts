import { describe, expect, it } from 'vitest'
import { formatPln } from '@/shared/lib/money'

describe('formatPln', () => {
  it('formats amounts with pl-PL PLN currency', () => {
    const formatted = formatPln(1234.5)
    expect(formatted).toMatch(/1[\s\u00a0]?234/)
    expect(formatted).toMatch(/PLN|zł/i)
  })

  it('formats zero', () => {
    expect(formatPln(0)).toMatch(/0/)
  })
})
