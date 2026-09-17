import { Chip } from '@mui/material'
import { rateSourceLabel, type RateSource } from '@/features/admin/lib/rateSource'

type RateSourceBadgeProps = {
  source: RateSource | undefined | null
  'data-testid'?: string
}

export function RateSourceBadge({ source, 'data-testid': testId }: RateSourceBadgeProps) {
  const label = rateSourceLabel(source)
  return (
    <Chip
      size="small"
      label={label}
      sx={{ mt: 0.5, height: 20 }}
      data-testid={testId ?? `rate-source-${label}`}
    />
  )
}
