import { Button, Stack, Typography } from '@mui/material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { BookingLayout } from '@/features/booking/components/BookingLayout'
import { SearchForm } from '@/features/booking/components/SearchForm'
import type { SearchStayValues } from '@/features/booking/schemas/bookingSchemas'
import { useI18n } from '@/shared/i18n/useI18n'

export function BookingHomePage() {
  const navigate = useNavigate()
  const { t } = useI18n()

  function onSearch(values: SearchStayValues) {
    const params = new URLSearchParams({
      checkIn: values.checkIn,
      checkOut: values.checkOut,
      guests: String(values.guests),
    })
    void navigate(`/booking?${params.toString()}`)
  }

  return (
    <BookingLayout>
      <Typography variant="h2" component="h1" gutterBottom>
        {t.booking.homeTitle}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 4, maxWidth: '36rem' }}>
        {t.booking.homeSubtitle}
      </Typography>
      <SearchForm onSubmit={onSearch} />
      <Stack direction="row" spacing={2} sx={{ mt: 4 }}>
        <Button component={RouterLink} to="/booking/manage" variant="outlined">
          {t.booking.manageCta}
        </Button>
      </Stack>
    </BookingLayout>
  )
}
