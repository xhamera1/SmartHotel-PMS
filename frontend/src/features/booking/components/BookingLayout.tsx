import { AppBar, Box, Button, Container, Toolbar, Typography } from '@mui/material'
import type { ReactNode } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useI18n } from '@/shared/i18n/useI18n'
import { AppChromeControls } from '@/shared/ui/AppChromeControls'
import { MainContent } from '@/shared/ui/MainContent'
import { SkipToContent } from '@/shared/ui/SkipToContent'

export function BookingLayout({ children }: { children: ReactNode }) {
  const { t } = useI18n()

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <SkipToContent />
      <AppBar
        position="sticky"
        color="transparent"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: 'divider' }}
        component="header"
      >
        <Toolbar sx={{ gap: 2, flexWrap: 'wrap' }} component="nav" aria-label={t.nav.publicAria}>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{
              flexGrow: 1,
              textDecoration: 'none',
              color: 'primary.main',
              fontFamily: 'Fraunces, serif',
            }}
          >
            {t.hotelName}
          </Typography>
          <Button component={RouterLink} to="/booking" color="primary">
            {t.nav.search}
          </Button>
          <Button component={RouterLink} to="/booking/manage" color="primary">
            {t.nav.myBooking}
          </Button>
          <Button component={RouterLink} to="/admin/login" color="inherit">
            {t.nav.staff}
          </Button>
          <AppChromeControls tone="primary" />
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ py: { xs: 4, md: 6 } }}>
        <MainContent>{children}</MainContent>
      </Container>
    </Box>
  )
}
