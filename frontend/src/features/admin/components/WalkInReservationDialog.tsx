import { zodResolver } from '@hookform/resolvers/zod'
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import {
  adminKeys,
  createAdminReservation,
  fetchRatePlans,
  fetchRoomTypes,
} from '@/features/admin/api/adminApi'
import { problemMessage } from '@/shared/api/problem'
import type { Messages } from '@/shared/i18n/messages'
import { useI18n } from '@/shared/i18n/useI18n'
import { addHotelDays, isHotelDate, nightsBetween, todayHotelDate } from '@/shared/lib/hotelDates'

type ValidationMessages = Messages['validation']

function createWalkInSchema(v: ValidationMessages) {
  return z
    .object({
      roomTypeCode: z.string().min(1, v.roomTypeRequired),
      ratePlanCode: z.string().min(1, v.ratePlanRequired),
      checkIn: z.string().min(1, v.checkInRequired).refine(isHotelDate, v.checkInInvalid),
      checkOut: z.string().min(1, v.checkOutRequired).refine(isHotelDate, v.checkOutInvalid),
      adults: z.number().int(v.guestsInt).min(1, v.guestsMin).max(10, v.guestsMax),
      firstName: z.string().trim().min(1, v.firstName).max(80),
      lastName: z.string().trim().min(1, v.lastName).max(80),
      email: z.email(v.email).max(255),
      phone: z.string().trim().max(30).optional(),
    })
    .superRefine((value, ctx) => {
      if (!isHotelDate(value.checkIn) || !isHotelDate(value.checkOut)) {
        return
      }
      if (nightsBetween(value.checkIn, value.checkOut) < 1) {
        ctx.addIssue({
          code: 'custom',
          path: ['checkOut'],
          message: v.checkOutAfter,
        })
      }
    })
}

type WalkInValues = z.infer<ReturnType<typeof createWalkInSchema>>

type WalkInReservationDialogProps = {
  open: boolean
  onClose: () => void
  listParams: Record<string, unknown>
}

export function WalkInReservationDialog({
  open,
  onClose,
  listParams,
}: WalkInReservationDialogProps) {
  const { t } = useI18n()
  const queryClient = useQueryClient()
  const today = todayHotelDate()
  const walkInSchema = useMemo(() => createWalkInSchema(t.validation), [t.validation])

  const form = useForm<WalkInValues>({
    resolver: zodResolver(walkInSchema),
    defaultValues: {
      roomTypeCode: '',
      ratePlanCode: '',
      checkIn: today,
      checkOut: addHotelDays(today, 1),
      adults: 2,
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
    },
  })

  const typesQuery = useQuery({
    queryKey: adminKeys.roomTypes({ page: 0, size: 100, active: true }),
    queryFn: () => fetchRoomTypes({ page: 0, size: 100, active: true }),
    enabled: open,
  })
  const plansQuery = useQuery({
    queryKey: adminKeys.ratePlans,
    queryFn: fetchRatePlans,
    enabled: open,
  })

  useEffect(() => {
    if (!open) {
      return
    }
    const firstType = typesQuery.data?.content?.[0]?.code
    const firstPlan = plansQuery.data?.[0]?.code
    if (firstType && !form.getValues('roomTypeCode')) {
      form.setValue('roomTypeCode', firstType)
    }
    if (firstPlan && !form.getValues('ratePlanCode')) {
      form.setValue('ratePlanCode', firstPlan)
    }
  }, [open, typesQuery.data, plansQuery.data, form])

  const createMutation = useMutation({
    mutationFn: (values: WalkInValues) =>
      createAdminReservation({
        roomTypeCode: values.roomTypeCode,
        ratePlanCode: values.ratePlanCode,
        checkIn: values.checkIn,
        checkOut: values.checkOut,
        adults: values.adults,
        guest: {
          firstName: values.firstName,
          lastName: values.lastName,
          email: values.email,
          phone: values.phone || undefined,
        },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: adminKeys.reservations(listParams) })
      form.reset({
        roomTypeCode: typesQuery.data?.content?.[0]?.code ?? '',
        ratePlanCode: plansQuery.data?.[0]?.code ?? '',
        checkIn: today,
        checkOut: addHotelDays(today, 1),
        adults: 2,
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
      })
      onClose()
    },
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = form

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" data-testid="walk-in-dialog">
      <DialogTitle>{t.admin.walkInTitle}</DialogTitle>
      <DialogContent>
        <Stack
          component="form"
          id="walk-in-form"
          spacing={2}
          sx={{ pt: 1 }}
          onSubmit={handleSubmit((values) => createMutation.mutate(values))}
        >
          {createMutation.isError ? (
            <Alert severity="error">
              {problemMessage(createMutation.error, t.admin.walkInCreateFailed)}
            </Alert>
          ) : null}
          <TextField
            select
            label={t.admin.roomType}
            {...register('roomTypeCode')}
            error={Boolean(errors.roomTypeCode)}
            helperText={errors.roomTypeCode?.message}
            data-testid="walk-in-room-type"
          >
            {(typesQuery.data?.content ?? []).map((rt) => (
              <MenuItem key={rt.code} value={rt.code ?? ''}>
                {rt.code} — {rt.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label={t.admin.ratePlan}
            {...register('ratePlanCode')}
            error={Boolean(errors.ratePlanCode)}
            helperText={errors.ratePlanCode?.message}
            data-testid="walk-in-rate-plan"
          >
            {(plansQuery.data ?? []).map((p) => (
              <MenuItem key={p.code} value={p.code ?? ''}>
                {p.code} — {p.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            type="date"
            label={t.booking.checkIn}
            {...register('checkIn')}
            error={Boolean(errors.checkIn)}
            helperText={errors.checkIn?.message}
            slotProps={{ inputLabel: { shrink: true } }}
            data-testid="walk-in-check-in"
          />
          <TextField
            type="date"
            label={t.booking.checkOut}
            {...register('checkOut')}
            error={Boolean(errors.checkOut)}
            helperText={errors.checkOut?.message}
            slotProps={{ inputLabel: { shrink: true } }}
            data-testid="walk-in-check-out"
          />
          <TextField
            type="number"
            label={t.admin.adults}
            {...register('adults', { valueAsNumber: true })}
            error={Boolean(errors.adults)}
            helperText={errors.adults?.message}
            data-testid="walk-in-adults"
          />
          <TextField
            label={t.booking.firstName}
            {...register('firstName')}
            error={Boolean(errors.firstName)}
            helperText={errors.firstName?.message}
            data-testid="walk-in-first-name"
          />
          <TextField
            label={t.booking.lastName}
            {...register('lastName')}
            error={Boolean(errors.lastName)}
            helperText={errors.lastName?.message}
            data-testid="walk-in-last-name"
          />
          <TextField
            label={t.common.email}
            type="email"
            {...register('email')}
            error={Boolean(errors.email)}
            helperText={errors.email?.message}
            data-testid="walk-in-email"
          />
          <TextField
            label={t.common.optionalPhone}
            {...register('phone')}
            error={Boolean(errors.phone)}
            helperText={errors.phone?.message}
            data-testid="walk-in-phone"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t.common.cancel}</Button>
        <Button
          type="submit"
          form="walk-in-form"
          variant="contained"
          disabled={createMutation.isPending}
          data-testid="walk-in-submit"
        >
          {t.admin.walkInSubmit}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
