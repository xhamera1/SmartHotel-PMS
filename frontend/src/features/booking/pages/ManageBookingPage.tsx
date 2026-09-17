import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'
import {
  bookingKeys,
  cancelReservation,
  lookupReservation,
} from '@/features/booking/api/bookingApi'
import { BookingLayout } from '@/features/booking/components/BookingLayout'
import { ReservationSummary } from '@/features/booking/components/ReservationSummary'
import {
  createManageLookupSchema,
  type ManageLookupValues,
} from '@/features/booking/schemas/bookingSchemas'
import { isProblemType } from '@/shared/api/problem'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

export function ManageBookingPage() {
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const { t } = useI18n()
  const codeParam = params.get('code') ?? ''
  const emailParam = params.get('email') ?? ''

  const manageLookupSchema = useMemo(() => createManageLookupSchema(t.validation), [t.validation])

  const form = useForm<ManageLookupValues>({
    resolver: zodResolver(manageLookupSchema),
    defaultValues: { code: codeParam, email: emailParam },
  })

  useEffect(() => {
    form.reset({ code: codeParam, email: emailParam })
  }, [codeParam, emailParam, form])

  const lookupKey = codeParam && emailParam ? bookingKeys.reservation(codeParam, emailParam) : null

  const lookupQuery = useQuery({
    queryKey: lookupKey ?? ['reservation', 'idle'],
    queryFn: () => lookupReservation(codeParam, emailParam),
    enabled: Boolean(codeParam && emailParam),
  })

  const cancelMutation = useMutation({
    mutationFn: () => cancelReservation(codeParam, emailParam),
    onSuccess: (reservation) => {
      if (lookupKey) {
        queryClient.setQueryData(lookupKey, reservation)
      }
    },
  })

  const reservation = lookupQuery.data
  const canCancel = reservation?.status === 'CONFIRMED' && reservation.ratePlan?.refundable === true

  return (
    <BookingLayout>
      <Typography variant="h3" component="h1" gutterBottom>
        {t.booking.manageTitle}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {t.booking.manageHint}
      </Typography>

      <Box
        component="form"
        noValidate
        data-testid="manage-lookup-form"
        onSubmit={form.handleSubmit((values) => {
          setParams({ code: values.code, email: values.email })
        })}
        sx={{ display: 'grid', gap: 2, maxWidth: 480, mb: 4 }}
      >
        <TextField
          label={t.booking.confirmationCode}
          {...form.register('code')}
          error={Boolean(form.formState.errors.code)}
          helperText={form.formState.errors.code?.message}
          slotProps={{ htmlInput: { style: { textTransform: 'uppercase' } } }}
          data-testid="manage-code"
        />
        <TextField
          label={t.common.email}
          type="email"
          {...form.register('email')}
          error={Boolean(form.formState.errors.email)}
          helperText={form.formState.errors.email?.message}
          data-testid="manage-email"
        />
        <Button type="submit" variant="contained" data-testid="manage-lookup-submit">
          {t.booking.findBooking}
        </Button>
      </Box>

      {lookupQuery.isFetching ? <PageSkeleton variant="form" rows={3} /> : null}

      {lookupQuery.isError ? (
        <Box sx={{ mb: 2 }}>
          <ProblemAlert
            error={lookupQuery.error}
            fallback={t.booking.lookupError}
            data-testid="manage-lookup-error"
          />
        </Box>
      ) : null}

      {!codeParam && !emailParam && !lookupQuery.isFetching ? (
        <EmptyState
          title={t.booking.manageEmptyTitle}
          description={t.booking.manageEmptyDesc}
          data-testid="manage-empty-prompt"
        />
      ) : null}

      {reservation ? (
        <Stack spacing={2}>
          <ReservationSummary reservation={reservation} />

          {reservation.status === 'CANCELLED' ? (
            <Alert severity="info">{t.booking.alreadyCancelled}</Alert>
          ) : null}

          {reservation.status === 'CONFIRMED' && reservation.ratePlan?.refundable === false ? (
            <Alert severity="warning" data-testid="non-refundable-notice">
              {t.booking.nonRefundableNotice}
            </Alert>
          ) : null}

          {canCancel ? (
            <Box>
              <Button
                color="secondary"
                variant="outlined"
                disabled={cancelMutation.isPending}
                onClick={() => cancelMutation.mutate()}
                data-testid="cancel-booking"
              >
                {cancelMutation.isPending ? t.booking.cancelling : t.booking.cancelBooking}
              </Button>
            </Box>
          ) : null}

          {cancelMutation.isError ? (
            <ProblemAlert
              error={cancelMutation.error}
              fallback={
                isProblemType(cancelMutation.error, '/rate-plan-not-refundable')
                  ? t.booking.cancelNonRefundable
                  : t.booking.cancelFailed
              }
              data-testid="cancel-error"
            />
          ) : null}

          {cancelMutation.isSuccess ? (
            <Alert severity="success" data-testid="cancel-success">
              {t.booking.cancelSuccess}
            </Alert>
          ) : null}
        </Stack>
      ) : null}
    </BookingLayout>
  )
}
