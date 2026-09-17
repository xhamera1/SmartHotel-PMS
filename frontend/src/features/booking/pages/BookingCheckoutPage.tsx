import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Box, Button, Stack, Typography } from '@mui/material'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom'
import {
  bookingKeys,
  createReservation,
  fetchAvailability,
} from '@/features/booking/api/bookingApi'
import { BookingLayout } from '@/features/booking/components/BookingLayout'
import { GuestDetailsFormFields } from '@/features/booking/components/GuestDetailsFormFields'
import {
  createGuestDetailsSchema,
  searchStaySchema,
  type GuestDetailsValues,
} from '@/features/booking/schemas/bookingSchemas'
import { isProblemType } from '@/shared/api/problem'
import { useI18n } from '@/shared/i18n/useI18n'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'
import { formatHotelDateDisplay } from '@/shared/lib/hotelDates'
import { formatPln } from '@/shared/lib/money'

export function BookingCheckoutPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { t, tf } = useI18n()

  const guestDetailsSchema = useMemo(() => createGuestDetailsSchema(t.validation), [t.validation])

  const stay = searchStaySchema.safeParse({
    checkIn: params.get('checkIn') ?? '',
    checkOut: params.get('checkOut') ?? '',
    guests: Number(params.get('guests') ?? Number.NaN),
  })
  const roomType = params.get('roomType') ?? ''
  const ratePlan = params.get('ratePlan') ?? ''
  const ratePlanName = params.get('ratePlanName') ?? ratePlan
  const totalFromQuery = Number(params.get('total') ?? '0')

  const selectionValid = stay.success && Boolean(roomType) && Boolean(ratePlan)

  const availabilityQuery = useQuery({
    queryKey: stay.success
      ? bookingKeys.availability(stay.data.checkIn, stay.data.checkOut, stay.data.guests)
      : ['availability', 'checkout-idle'],
    queryFn: () => fetchAvailability(stay.data!.checkIn, stay.data!.checkOut, stay.data!.guests),
    enabled: selectionValid,
  })

  const liveQuote = availabilityQuery.data?.roomTypes
    ?.find((rt) => rt.code === roomType)
    ?.ratePlans?.find((rp) => rp.code === ratePlan)
  const totalPrice = liveQuote?.totalPrice ?? totalFromQuery

  const form = useForm<GuestDetailsValues>({
    resolver: zodResolver(guestDetailsSchema),
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      paymentAuthorized: false,
    },
  })

  const bookingMutation = useMutation({
    mutationFn: createReservation,
    onSuccess: (reservation) => {
      const code = reservation.confirmationCode
      const email = form.getValues('email')
      if (!code || !email) {
        return
      }
      void navigate(
        `/booking/confirmation?code=${encodeURIComponent(code)}&email=${encodeURIComponent(email)}`,
        { state: { reservation } },
      )
    },
  })

  if (!selectionValid) {
    return (
      <BookingLayout>
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t.booking.checkoutMissing}
        </Alert>
        <Button component={RouterLink} to="/booking" variant="contained">
          {t.booking.searchAgain}
        </Button>
      </BookingLayout>
    )
  }

  const stayData = stay.data

  return (
    <BookingLayout>
      <Typography variant="h3" component="h1" gutterBottom>
        {t.booking.checkoutTitle}
      </Typography>

      <Box
        sx={{
          border: 1,
          borderColor: 'divider',
          borderRadius: 2,
          p: 2,
          mb: 3,
          bgcolor: 'background.paper',
        }}
        data-testid="checkout-selection"
      >
        <Typography>
          {formatHotelDateDisplay(stayData.checkIn)} → {formatHotelDateDisplay(stayData.checkOut)} ·{' '}
          {tf(t.booking.guestsCount, { count: stayData.guests })}
        </Typography>
        <Typography sx={{ mt: 0.5 }}>
          {roomType} · {ratePlanName} ({ratePlan})
        </Typography>
        <Typography variant="h5" sx={{ mt: 1 }}>
          {formatPln(totalPrice)}
        </Typography>
      </Box>

      <FormProvider {...form}>
        <Box
          component="form"
          noValidate
          onSubmit={form.handleSubmit((values) => {
            bookingMutation.mutate({
              roomTypeCode: roomType,
              ratePlanCode: ratePlan,
              checkIn: stayData.checkIn,
              checkOut: stayData.checkOut,
              adults: stayData.guests,
              guest: {
                firstName: values.firstName,
                lastName: values.lastName,
                email: values.email,
                phone: values.phone || undefined,
              },
            })
          })}
        >
          <GuestDetailsFormFields totalPrice={totalPrice} />

          {bookingMutation.isError ? (
            <Box sx={{ mt: 2 }}>
              <ProblemAlert
                error={bookingMutation.error}
                fallback={
                  isProblemType(bookingMutation.error, '/room-no-longer-available')
                    ? t.booking.roomFilled
                    : t.booking.bookingFailed
                }
                data-testid="checkout-error"
              />
            </Box>
          ) : null}

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 3 }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={bookingMutation.isPending}
              data-testid="confirm-booking"
            >
              {bookingMutation.isPending ? t.booking.reserving : t.booking.payAndBook}
            </Button>
            <Button component={RouterLink} to={`/booking?${params.toString()}`} variant="outlined">
              {t.booking.backToResults}
            </Button>
          </Stack>
        </Box>
      </FormProvider>
    </BookingLayout>
  )
}
