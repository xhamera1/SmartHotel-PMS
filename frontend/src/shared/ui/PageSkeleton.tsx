import { Box, Skeleton, Stack } from '@mui/material'
import { testIds } from '@/shared/ui/testids'

type PageSkeletonProps = {
  variant?: 'cards' | 'table' | 'chart' | 'form'
  rows?: number
  'data-testid'?: string
}

export function PageSkeleton({
  variant = 'table',
  rows = 4,
  'data-testid': dataTestId = testIds.loadingSkeleton,
}: PageSkeletonProps) {
  if (variant === 'cards') {
    return (
      <Box
        data-testid={dataTestId}
        aria-busy="true"
        aria-label="Loading"
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' },
        }}
      >
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} variant="rounded" height={110} />
        ))}
      </Box>
    )
  }

  if (variant === 'chart') {
    return (
      <Box data-testid={dataTestId} aria-busy="true" aria-label="Loading chart">
        <Skeleton variant="text" width="40%" height={36} />
        <Skeleton variant="rounded" height={280} sx={{ mt: 1 }} />
      </Box>
    )
  }

  if (variant === 'form') {
    return (
      <Stack spacing={2} data-testid={dataTestId} aria-busy="true" aria-label="Loading form">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} variant="rounded" height={56} />
        ))}
      </Stack>
    )
  }

  return (
    <Stack spacing={1} data-testid={dataTestId} aria-busy="true" aria-label="Loading table">
      <Skeleton variant="rounded" height={40} />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="rounded" height={48} />
      ))}
    </Stack>
  )
}
