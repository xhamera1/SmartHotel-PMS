import { Box, Chip, Stack, Typography } from '@mui/material'
import type { components } from '@/shared/api/schema'
import { useI18n } from '@/shared/i18n/useI18n'
import { formatHotelDateDisplay } from '@/shared/lib/hotelDates'
import { formatPln } from '@/shared/lib/money'

type Reservation = components['schemas']['ReservationResponse']

type ReservationSummaryProps = {
  reservation: Reservation
  title?: string
}

export function ReservationSummary({ reservation, title }: ReservationSummaryProps) {
  const { t, tf } = useI18n()
  const breakdown = reservation.priceBreakdown ?? []
  const heading = title ?? t.booking.summaryTitle

  const statusLabel = reservation.status != null ? t.status[reservation.status] : undefined

  return (
    <Box
      data-testid="reservation-summary"
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        p: 2.5,
        bgcolor: 'background.paper',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 1,
          mb: 2,
        }}
      >
        <Typography variant="h5" component="h2">
          {heading}
        </Typography>
        {statusLabel ? <Chip label={statusLabel} color="primary" variant="outlined" /> : null}
      </Box>

      {reservation.confirmationCode ? (
        <Typography sx={{ mb: 1 }}>
          {t.booking.code}:{' '}
          <strong data-testid="confirmation-code">{reservation.confirmationCode}</strong>
        </Typography>
      ) : null}

      <Typography color="text.secondary">
        {reservation.checkIn ? formatHotelDateDisplay(reservation.checkIn) : '—'}
        {' → '}
        {reservation.checkOut ? formatHotelDateDisplay(reservation.checkOut) : '—'}
        {reservation.adults != null
          ? ` · ${tf(t.booking.guestsCount, { count: reservation.adults })}`
          : null}
      </Typography>
      <Typography sx={{ mt: 0.5 }}>
        {t.booking.room}: {reservation.roomType ?? '—'}
        {reservation.ratePlan?.code ? ` · ${t.booking.rate} ${reservation.ratePlan.code}` : ''}
        {reservation.ratePlan?.refundable === false
          ? ` (${t.booking.nonRefundable})`
          : reservation.ratePlan?.refundable
            ? ` (${t.booking.refundable})`
            : ''}
      </Typography>

      {breakdown.length > 0 ? (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t.booking.priceBreakdown}
          </Typography>
          <Stack component="ul" sx={{ m: 0, pl: 2 }} spacing={0.5}>
            {breakdown.map((line) => (
              <Typography component="li" key={line.date} variant="body2">
                {line.date ? formatHotelDateDisplay(line.date) : '—'}
                {': '}
                <strong>{formatPln(line.price ?? 0)}</strong>
                {line.barPrice != null ? ` (BAR ${formatPln(line.barPrice)})` : null}
              </Typography>
            ))}
          </Stack>
        </Box>
      ) : null}

      <Typography variant="h5" sx={{ mt: 2 }}>
        {t.booking.total}: {formatPln(reservation.totalPrice ?? 0)}
      </Typography>
    </Box>
  )
}
