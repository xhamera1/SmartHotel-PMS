import { Alert, Box, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material'
import { Controller, useFormContext } from 'react-hook-form'
import type { GuestDetailsValues } from '@/features/booking/schemas/bookingSchemas'
import { useI18n } from '@/shared/i18n/useI18n'
import { formatPln } from '@/shared/lib/money'

type GuestDetailsFormFieldsProps = {
  totalPrice: number
}

export function GuestDetailsFormFields({ totalPrice }: GuestDetailsFormFieldsProps) {
  const { t, tf } = useI18n()
  const {
    register,
    control,
    formState: { errors },
  } = useFormContext<GuestDetailsValues>()

  const amountLabel = formatPln(totalPrice)

  return (
    <Stack spacing={2} data-testid="guest-details-form">
      <Typography variant="h5" component="h2">
        {t.booking.guestDetails}
      </Typography>
      <TextField
        label={t.booking.firstName}
        {...register('firstName')}
        error={Boolean(errors.firstName)}
        helperText={errors.firstName?.message}
        autoComplete="given-name"
        data-testid="guest-first-name"
      />
      <TextField
        label={t.booking.lastName}
        {...register('lastName')}
        error={Boolean(errors.lastName)}
        helperText={errors.lastName?.message}
        autoComplete="family-name"
        data-testid="guest-last-name"
      />
      <TextField
        label={t.common.email}
        type="email"
        {...register('email')}
        error={Boolean(errors.email)}
        helperText={errors.email?.message}
        autoComplete="email"
        data-testid="guest-email"
      />
      <TextField
        label={t.common.optionalPhone}
        {...register('phone')}
        error={Boolean(errors.phone)}
        helperText={errors.phone?.message}
        autoComplete="tel"
        data-testid="guest-phone"
      />

      <Box
        sx={{
          border: 1,
          borderColor: 'divider',
          borderRadius: 2,
          p: 2,
          bgcolor: 'background.paper',
        }}
        data-testid="mock-payment-panel"
      >
        <Typography variant="h6" gutterBottom>
          {t.booking.mockPayment}
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 1 }}>
          {t.booking.mockPaymentHint}
        </Typography>
        <Typography variant="h5" sx={{ mb: 1 }}>
          {amountLabel}
        </Typography>
        <Controller
          name="paymentAuthorized"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              control={
                <Checkbox
                  checked={Boolean(field.value)}
                  onChange={(e) => field.onChange(e.target.checked)}
                  slotProps={{ input: { 'aria-label': t.booking.authorizePaymentAria } }}
                  data-testid="mock-payment-authorize"
                />
              }
              label={tf(t.booking.authorizePayment, { amount: amountLabel })}
            />
          )}
        />
        {errors.paymentAuthorized ? (
          <Alert severity="error" sx={{ mt: 1 }}>
            {errors.paymentAuthorized.message}
          </Alert>
        ) : null}
      </Box>
    </Stack>
  )
}
