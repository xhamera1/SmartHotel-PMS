import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { RateSourceBadge } from '@/features/admin/components/RateSourceBadge'
import {
  RATE_SOURCE_LABEL,
  rateSourceLabel,
  type RateSource,
} from '@/features/admin/lib/rateSource'

describe('rateSourceLabel', () => {
  it.each(Object.entries(RATE_SOURCE_LABEL) as Array<[RateSource, string]>)(
    'maps %s → %s',
    (source, label) => {
      expect(rateSourceLabel(source)).toBe(label)
    },
  )

  it('defaults missing source to BASE', () => {
    expect(rateSourceLabel(undefined)).toBe('BASE')
    expect(rateSourceLabel(null)).toBe('BASE')
  })
})

describe('RateSourceBadge', () => {
  it.each(Object.entries(RATE_SOURCE_LABEL) as Array<[RateSource, string]>)(
    'renders chip for %s',
    (source, label) => {
      render(<RateSourceBadge source={source} />)
      expect(screen.getByTestId(`rate-source-${label}`)).toHaveTextContent(label)
    },
  )
})
