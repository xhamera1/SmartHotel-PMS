import type { RateCalendarDay } from '@/features/admin/api/adminApi'

export type RateSource = NonNullable<RateCalendarDay['source']>

export const RATE_SOURCE_LABEL: Record<RateSource, string> = {
  ML_MODEL: 'ML',
  MANUAL: 'MANUAL',
  BASE: 'BASE',
  BASE_FALLBACK: 'FALLBACK',
}

export function rateSourceLabel(source: RateSource | undefined | null): string {
  if (!source) {
    return RATE_SOURCE_LABEL.BASE
  }
  return RATE_SOURCE_LABEL[source]
}
