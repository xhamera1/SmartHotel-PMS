import { zodResolver } from '@hookform/resolvers/zod'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
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
import { todayHotelDate } from '@/shared/lib/hotelDates'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

export function ManageBookingPage() {
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const { t } = useI18n()
  const [confirmOpen, setConfirmOpen] = useState(false)
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
      setConfirmOpen(false)
      if (lookupKey) {
        queryClient.setQueryData(lookupKey, reservation)
      }
    },
  })
  const resetCancel = cancelMutation.reset

  useEffect(() => {
    resetCancel()
    setConfirmOpen(false)
  }, [codeParam, emailParam, resetCancel])

  const reservation = lookupQuery.data
  const hotelToday = todayHotelDate()
  const withinCancelWindow =
    Boolean(reservation?.checkIn) && hotelToday <= (reservation?.checkIn ?? '')
  const canCancel =
    reservation?.status === 'CONFIRMED' &&
    reservation.ratePlan?.refundable === true &&
    withinCancelWindow
  const cancelWindowClosed =
    reservation?.status === 'CONFIRMED' &&
    reservation.ratePlan?.refundable === true &&
    !withinCancelWindow
  const showAlreadyCancelled =
    reservation?.status === 'CANCELLED' && !cancelMutation.isSuccess

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

          {showAlreadyCancelled ? (
            <Alert severity="info" data-testid="already-cancelled">
              {t.booking.alreadyCancelled}
            </Alert>
          ) : null}

          {reservation.status === 'CONFIRMED' && reservation.ratePlan?.refundable === false ? (
            <Alert severity="warning" data-testid="non-refundable-notice">
              {t.booking.nonRefundableNotice}
            </Alert>
          ) : null}

          {cancelWindowClosed ? (
            <Alert severity="info" data-testid="cancel-window-closed">
              {t.booking.cancelWindowClosed}
            </Alert>
          ) : null}

          {canCancel ? (
            <Box>
              <Button
                color="secondary"
                variant="outlined"
                disabled={cancelMutation.isPending}
                onClick={() => setConfirmOpen(true)}
                data-testid="cancel-booking"
              >
                {t.booking.cancelBooking}
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

      <Dialog
        open={confirmOpen}
        onClose={() => (cancelMutation.isPending ? undefined : setConfirmOpen(false))}
        aria-labelledby="cancel-confirm-title"
        data-testid="cancel-confirm-dialog"
      >
        <DialogTitle id="cancel-confirm-title">{t.booking.cancelConfirmTitle}</DialogTitle>
        <DialogContent>
          <DialogContentText>{t.booking.cancelConfirmBody}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setConfirmOpen(false)}
            disabled={cancelMutation.isPending}
            data-testid="cancel-confirm-dismiss"
          >
            {t.common.cancel}
          </Button>
          <Button
            color="secondary"
            variant="contained"
            disabled={cancelMutation.isPending}
            onClick={() => cancelMutation.mutate()}
            data-testid="cancel-confirm-submit"
          >
            {cancelMutation.isPending ? t.booking.cancelling : t.booking.cancelConfirmAction}
          </Button>
        </DialogActions>
      </Dialog>
    </BookingLayout>
  )
}
