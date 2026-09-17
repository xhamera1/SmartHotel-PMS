import { Link } from '@mui/material'
import { useI18n } from '@/shared/i18n/useI18n'
import { testIds } from '@/shared/ui/testids'

/** First focusable control for keyboard users — jumps past chrome into main. */
export function SkipToContent({ href = '#main-content' }: { href?: string }) {
  const { t } = useI18n()
  return (
    <Link
      href={href}
      data-testid={testIds.skipToContent}
      underline="always"
      sx={{
        position: 'absolute',
        left: 16,
        top: 16,
        zIndex: 2000,
        px: 2,
        py: 1,
        bgcolor: 'background.paper',
        borderRadius: 1,
        transform: 'translateY(-200%)',
        transition: 'transform 0.15s ease',
        '&:focus': {
          transform: 'translateY(0)',
          outline: '3px solid',
          outlineColor: 'secondary.main',
          outlineOffset: 2,
        },
      }}
    >
      {t.common.skipToContent}
    </Link>
  )
}
