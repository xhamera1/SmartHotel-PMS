import { Stack, Typography } from '@mui/material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { bookingKeys, fetchAvailability } from '@/features/booking/api/bookingApi'
import { BookingLayout } from '@/features/booking/components/BookingLayout'
import { RoomTypeCard } from '@/features/booking/components/RoomTypeCard'
import { SearchForm } from '@/features/booking/components/SearchForm'
import { searchStaySchema, type SearchStayValues } from '@/features/booking/schemas/bookingSchemas'
import type { components } from '@/shared/api/schema'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

type RatePlan = NonNullable<
  NonNullable<components['schemas']['AvailabilityResponse']['roomTypes']>[number]['ratePlans']
>[number]

export function BookingSearchPage() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const { t } = useI18n()

  const draft = useMemo(() => {
    const guestsRaw = params.get('guests')
    const guests = guestsRaw == null || guestsRaw === '' ? NaN : Number(guestsRaw)
    const parsed = searchStaySchema.safeParse({
      checkIn: params.get('checkIn') ?? '',
      checkOut: params.get('checkOut') ?? '',
      guests,
    })
    return parsed.success ? parsed.data : null
  }, [params])

  const availabilityQuery = useQuery({
    queryKey: draft
      ? bookingKeys.availability(draft.checkIn, draft.checkOut, draft.guests)
      : ['availability', 'idle'],
    queryFn: () => fetchAvailability(draft!.checkIn, draft!.checkOut, draft!.guests),
    enabled: Boolean(draft),
  })

  function onSearch(values: SearchStayValues) {
    setParams({
      checkIn: values.checkIn,
      checkOut: values.checkOut,
      guests: String(values.guests),
    })
  }

  function onSelect(roomTypeCode: string, ratePlan: RatePlan) {
    if (!draft || !ratePlan.code) {
      return
    }
    const next = new URLSearchParams({
      checkIn: draft.checkIn,
      checkOut: draft.checkOut,
      guests: String(draft.guests),
      roomType: roomTypeCode,
      ratePlan: ratePlan.code,
      total: String(ratePlan.totalPrice ?? 0),
      ratePlanName: ratePlan.name ?? ratePlan.code,
    })
    void navigate(`/booking/checkout?${next.toString()}`)
  }

  const roomTypes = availabilityQuery.data?.roomTypes ?? []

  return (
    <BookingLayout>
      <Typography variant="h3" component="h1" gutterBottom>
        {t.booking.searchTitle}
      </Typography>
      <SearchForm defaultValues={draft ?? undefined} onSubmit={onSearch} />

      <Stack spacing={2} sx={{ mt: 4 }} data-testid="availability-results">
        {!draft ? (
          <EmptyState
            title={t.booking.emptyDatesTitle}
            description={t.booking.emptyDatesDesc}
            data-testid="availability-empty-prompt"
          />
        ) : null}

        {draft && availabilityQuery.isFetching ? <PageSkeleton variant="cards" rows={3} /> : null}

        {availabilityQuery.isError ? (
          <ProblemAlert
            error={availabilityQuery.error}
            fallback={t.booking.availabilityError}
            data-testid="availability-error"
          />
        ) : null}

        {draft && availabilityQuery.isSuccess && roomTypes.length === 0 ? (
          <EmptyState
            title={t.booking.noRoomsTitle}
            description={t.booking.noRoomsDesc}
            data-testid="availability-empty"
          />
        ) : null}

        {!availabilityQuery.isFetching
          ? roomTypes.map((roomType) =>
              roomType.code ? (
                <RoomTypeCard
                  key={roomType.code}
                  roomType={roomType}
                  currency={availabilityQuery.data?.currency ?? 'PLN'}
                  onSelect={(plan) => onSelect(roomType.code!, plan)}
                />
              ) : null,
            )
          : null}
      </Stack>
    </BookingLayout>
  )
}
