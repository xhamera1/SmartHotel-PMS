import { zodResolver } from '@hookform/resolvers/zod'
import { Box, Button, MenuItem, TextField } from '@mui/material'
import { useMemo } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import {
  MAX_GUESTS,
  MIN_GUESTS,
  createSearchStaySchema,
  type SearchStayValues,
} from '@/features/booking/schemas/bookingSchemas'
import { useI18n } from '@/shared/i18n/useI18n'
import { addHotelDays, todayHotelDate } from '@/shared/lib/hotelDates'

type SearchFormProps = {
  defaultValues?: Partial<SearchStayValues>
  submitLabel?: string
  onSubmit: (values: SearchStayValues) => void
}

export function SearchForm({ defaultValues, submitLabel, onSubmit }: SearchFormProps) {
  const { t } = useI18n()
  const schema = useMemo(() => createSearchStaySchema(t.validation), [t.validation])
  const today = todayHotelDate()
  const maxCheckIn = addHotelDays(today, 365)
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SearchStayValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      checkIn: defaultValues?.checkIn ?? today,
      checkOut: defaultValues?.checkOut ?? addHotelDays(defaultValues?.checkIn ?? today, 2),
      guests: defaultValues?.guests ?? 2,
    },
  })

  const checkIn = useWatch({ control, name: 'checkIn' })
  const minCheckOut =
    checkIn && checkIn >= today ? addHotelDays(checkIn, 1) : addHotelDays(today, 1)

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      data-testid="booking-search-form"
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1.2fr 1.2fr 0.8fr auto' },
        alignItems: 'start',
      }}
    >
      <Controller
        name="checkIn"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            label={t.booking.checkIn}
            type="date"
            slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: today, max: maxCheckIn } }}
            error={Boolean(errors.checkIn)}
            helperText={errors.checkIn?.message}
            data-testid="search-check-in"
          />
        )}
      />
      <Controller
        name="checkOut"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            label={t.booking.checkOut}
            type="date"
            slotProps={{
              inputLabel: { shrink: true },
              htmlInput: { min: minCheckOut, max: addHotelDays(checkIn || today, 30) },
            }}
            error={Boolean(errors.checkOut)}
            helperText={errors.checkOut?.message}
            data-testid="search-check-out"
          />
        )}
      />
      <Controller
        name="guests"
        control={control}
        render={({ field }) => (
          <TextField
            select
            label={t.booking.guests}
            value={field.value}
            onChange={(e) => field.onChange(Number(e.target.value))}
            onBlur={field.onBlur}
            name={field.name}
            inputRef={field.ref}
            error={Boolean(errors.guests)}
            helperText={errors.guests?.message}
            data-testid="search-guests"
          >
            {Array.from({ length: MAX_GUESTS - MIN_GUESTS + 1 }, (_, i) => MIN_GUESTS + i).map(
              (n) => (
                <MenuItem key={n} value={n}>
                  {n}
                </MenuItem>
              ),
            )}
          </TextField>
        )}
      />
      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={isSubmitting}
        data-testid="search-submit"
      >
        {submitLabel ?? t.booking.searchSubmit}
      </Button>
    </Box>
  )
}
