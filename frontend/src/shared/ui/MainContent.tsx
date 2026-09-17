import { Box } from '@mui/material'
import type { ReactNode } from 'react'
import { testIds } from '@/shared/ui/testids'

/** Landmark wrapper for page content — target of SkipToContent. */
export function MainContent({
  children,
  'data-testid': dataTestId = testIds.mainContent,
}: {
  children: ReactNode
  'data-testid'?: string
}) {
  return (
    <Box
      component="main"
      id="main-content"
      tabIndex={-1}
      data-testid={dataTestId}
      sx={{
        outline: 'none',
        '&:focus-visible': { outline: '3px solid', outlineColor: 'secondary.main' },
      }}
    >
      {children}
    </Box>
  )
}
