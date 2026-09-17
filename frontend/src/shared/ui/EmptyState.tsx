import { Box, Button, Typography } from '@mui/material'
import type { ReactNode } from 'react'
import { testIds } from '@/shared/ui/testids'

type EmptyStateProps = {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  icon?: ReactNode
  'data-testid'?: string
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
  'data-testid': dataTestId = testIds.emptyState,
}: EmptyStateProps) {
  return (
    <Box
      role="status"
      data-testid={dataTestId}
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        bgcolor: 'background.paper',
        p: 4,
        textAlign: 'center',
      }}
    >
      {icon}
      <Typography variant="h6" component="h2" gutterBottom>
        {title}
      </Typography>
      {description ? (
        <Typography
          color="text.secondary"
          sx={{ mb: actionLabel ? 2 : 0, maxWidth: '36rem', mx: 'auto' }}
        >
          {description}
        </Typography>
      ) : null}
      {actionLabel && onAction ? (
        <Button variant="contained" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </Box>
  )
}
