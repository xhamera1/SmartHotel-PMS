import { Box, Button, Chip, Divider, Stack, Typography } from '@mui/material'
import type { components } from '@/shared/api/schema'
import { useI18n } from '@/shared/i18n/useI18n'
import { formatHotelDateDisplay } from '@/shared/lib/hotelDates'
import { formatPln } from '@/shared/lib/money'

type RoomType = NonNullable<components['schemas']['AvailabilityResponse']['roomTypes']>[number]
type RatePlan = NonNullable<RoomType['ratePlans']>[number]

type RoomTypeCardProps = {
  roomType: RoomType
  currency: string
  onSelect: (ratePlan: RatePlan) => void
}

export function RoomTypeCard({ roomType, currency, onSelect }: RoomTypeCardProps) {
  const { t, tf } = useI18n()
  const nights = roomType.nights ?? []
  const plans = roomType.ratePlans ?? []

  return (
    <Box
      component="article"
      data-testid={`room-type-card-${roomType.code ?? 'unknown'}`}
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        p: 2.5,
        bgcolor: 'background.paper',
        display: 'grid',
        gap: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          gap: 1,
        }}
      >
        <Box>
          <Typography variant="h5" component="h2">
            {roomType.name}
          </Typography>
          <Typography color="text.secondary">
            {tf(t.booking.roomMeta, {
              code: roomType.code ?? '',
              capacity: roomType.capacity ?? 0,
              roomsLeft: roomType.roomsLeft ?? 0,
            })}
          </Typography>
        </Box>
        <Chip label={currency || 'PLN'} size="small" />
      </Box>

      <Box>
        <Typography variant="subtitle2" gutterBottom>
          {t.booking.nightlyBar}
        </Typography>
        <Stack component="ul" sx={{ m: 0, pl: 2 }} spacing={0.5}>
          {nights.map((night) => (
            <Typography component="li" key={night.date} variant="body2">
              {night.date ? formatHotelDateDisplay(night.date) : '—'}
              {': '}
              <strong>{formatPln(night.bar ?? 0)}</strong>
              {night.priceSource ? ` (${night.priceSource})` : null}
            </Typography>
          ))}
        </Stack>
      </Box>

      <Divider />

      <Stack spacing={1.5}>
        <Typography variant="subtitle2">{t.booking.ratePlans}</Typography>
        {plans.map((plan) => (
          <Box
            key={plan.code}
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              alignItems: { sm: 'center' },
              justifyContent: 'space-between',
              gap: 1,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1.5,
              p: 1.5,
            }}
          >
            <Box>
              <Typography sx={{ fontWeight: 600 }}>{plan.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {plan.refundable ? t.booking.refundable : t.booking.nonRefundable}
                {plan.breakfastIncluded ? ` · ${t.booking.breakfast}` : ''}
              </Typography>
              <Typography variant="h6" component="p" sx={{ mt: 0.5 }}>
                {formatPln(plan.totalPrice ?? 0)}
              </Typography>
            </Box>
            <Button
              variant="contained"
              onClick={() => onSelect(plan)}
              data-testid={`select-rate-${roomType.code}-${plan.code}`}
            >
              {t.booking.select}
            </Button>
          </Box>
        ))}
      </Stack>
    </Box>
  )
}
