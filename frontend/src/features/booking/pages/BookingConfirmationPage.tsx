import { Button, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { Link as RouterLink, useLocation, useSearchParams } from 'react-router-dom'
import { bookingKeys, lookupReservation } from '@/features/booking/api/bookingApi'
import { BookingLayout } from '@/features/booking/components/BookingLayout'
import { ReservationSummary } from '@/features/booking/components/ReservationSummary'
import type { components } from '@/shared/api/schema'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

type Reservation = components['schemas']['ReservationResponse']

export function BookingConfirmationPage() {
  const [params] = useSearchParams()
  const location = useLocation()
  const { t } = useI18n()
  const code = params.get('code')?.trim() ?? ''
  const email = params.get('email')?.trim() ?? ''
  const fromState = (location.state as { reservation?: Reservation } | null)?.reservation

  const lookupQuery = useQuery({
    queryKey: bookingKeys.reservation(code, email),
    queryFn: () => lookupReservation(code, email),
    enabled: Boolean(code && email),
    initialData: fromState,
  })

  const reservation = lookupQuery.data

  return (
    <BookingLayout>
      <Typography variant="h3" component="h1" gutterBottom data-testid="confirmation-heading">
        {t.booking.confirmationTitle}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {t.booking.confirmationHint}
      </Typography>

      {lookupQuery.isFetching && !reservation ? <PageSkeleton variant="form" rows={4} /> : null}

      {lookupQuery.isError && !reservation ? (
        <ProblemAlert
          error={lookupQuery.error}
          fallback={t.booking.confirmationError}
          data-testid="confirmation-error"
        />
      ) : null}

      {!code || !email ? (
        <EmptyState
          title={t.booking.confirmationEmptyTitle}
          description={t.booking.confirmationEmptyDesc}
          data-testid="confirmation-empty"
        />
      ) : null}

      {reservation ? <ReservationSummary reservation={reservation} /> : null}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 3 }}>
        <Button
          component={RouterLink}
          to={
            code && email
              ? `/booking/manage?code=${encodeURIComponent(code)}&email=${encodeURIComponent(email)}`
              : '/booking/manage'
          }
          variant="contained"
          data-testid="go-manage-booking"
        >
          {t.booking.manageCta}
        </Button>
        <Button component={RouterLink} to="/" variant="outlined">
          {t.booking.home}
        </Button>
      </Stack>
    </BookingLayout>
  )
}
