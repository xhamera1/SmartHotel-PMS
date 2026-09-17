import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import {
  adminKeys,
  deleteManualRate,
  fetchRateCalendar,
  fetchRoomTypes,
  putManualRate,
  refreshPrices,
  type RateCalendarDay,
  type RoomType,
} from '@/features/admin/api/adminApi'
import { RateSourceBadge } from '@/features/admin/components/RateSourceBadge'
import { authSession } from '@/shared/auth/session'
import { problemMessage } from '@/shared/api/problem'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'
import { formatHotelDate, parseHotelDate, todayHotelDate } from '@/shared/lib/hotelDates'
import { formatPln } from '@/shared/lib/money'
import { endOfMonth, format, startOfMonth, eachDayOfInterval, getDay } from 'date-fns'
import { useSyncExternalStore } from 'react'

function heatColor(price: number, min: number, max: number): string {
  if (max <= min) {
    return 'rgba(15, 92, 92, 0.15)'
  }
  const t = Math.min(1, Math.max(0, (price - min) / (max - min)))
  const alpha = 0.12 + t * 0.55
  return `rgba(15, 92, 92, ${alpha.toFixed(3)})`
}

export function RateCalendarPage() {
  const { t, tf } = useI18n()
  const queryClient = useQueryClient()
  const role = useSyncExternalStore(authSession.subscribe, authSession.getRole, () => null)
  const isAdmin = role === 'ADMIN'

  const [month, setMonth] = useState(() => todayHotelDate().slice(0, 7))
  const [roomTypeCode, setRoomTypeCode] = useState('')
  const [selected, setSelected] = useState<RateCalendarDay | null>(null)
  const [overridePrice, setOverridePrice] = useState('')
  const [overrideError, setOverrideError] = useState<string | null>(null)
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null)

  const typesQuery = useQuery({
    queryKey: adminKeys.roomTypes({ page: 0, size: 100, active: true }),
    queryFn: () => fetchRoomTypes({ page: 0, size: 100, active: true }),
  })

  const selectedType: RoomType | undefined =
    (typesQuery.data?.content ?? []).find((t) => t.code === roomTypeCode) ??
    typesQuery.data?.content?.[0]

  const effectiveCode = roomTypeCode || selectedType?.code || ''

  const range = useMemo(() => {
    const anchor = parseHotelDate(`${month}-01`)
    const from = formatHotelDate(startOfMonth(anchor))
    const to = formatHotelDate(endOfMonth(anchor))
    return { from, to, anchor }
  }, [month])

  const calendarQuery = useQuery({
    queryKey: adminKeys.rateCalendar(effectiveCode, range.from, range.to),
    queryFn: () => fetchRateCalendar(effectiveCode, range.from, range.to),
    enabled: Boolean(effectiveCode),
  })

  const daysByDate = useMemo(() => {
    const map = new Map<string, RateCalendarDay>()
    for (const day of calendarQuery.data?.days ?? []) {
      if (day.date) {
        map.set(day.date, day)
      }
    }
    return map
  }, [calendarQuery.data])

  const monthDays = useMemo(() => {
    return eachDayOfInterval({ start: startOfMonth(range.anchor), end: endOfMonth(range.anchor) })
  }, [range.anchor])

  const prices = (calendarQuery.data?.days ?? []).map((d) => d.price ?? 0)
  const minPrice = prices.length ? Math.min(...prices) : 0
  const maxPrice = prices.length ? Math.max(...prices) : 0

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selected?.date || !effectiveCode) {
        throw new Error('Brak dnia')
      }
      const price = Number(overridePrice)
      const min = selectedType?.minPrice ?? 0
      const max = selectedType?.maxPrice ?? Number.POSITIVE_INFINITY
      if (!Number.isFinite(price)) {
        throw new Error(t.validation.priceRequired)
      }
      if (price < min || price > max) {
        throw new Error(t.validation.priceRange)
      }
      return putManualRate(effectiveCode, selected.date, price)
    },
    onSuccess: async () => {
      setSelected(null)
      await queryClient.invalidateQueries({
        queryKey: adminKeys.rateCalendar(effectiveCode, range.from, range.to),
      })
    },
    onError: (error) => {
      setOverrideError(
        error instanceof Error ? error.message : problemMessage(error, t.admin.saveFailed),
      )
    },
  })

  const clearMutation = useMutation({
    mutationFn: async () => {
      if (!selected?.date || !effectiveCode) {
        throw new Error('Brak dnia')
      }
      await deleteManualRate(effectiveCode, selected.date)
    },
    onSuccess: async () => {
      setSelected(null)
      await queryClient.invalidateQueries({
        queryKey: adminKeys.rateCalendar(effectiveCode, range.from, range.to),
      })
    },
  })

  const refreshMutation = useMutation({
    mutationFn: refreshPrices,
    onSuccess: async (res) => {
      setRefreshMsg(res.message ?? res.status ?? 'OK')
      if (effectiveCode) {
        await queryClient.invalidateQueries({
          queryKey: adminKeys.rateCalendar(effectiveCode, range.from, range.to),
        })
      }
    },
    onError: (error) => {
      setRefreshMsg(problemMessage(error, t.admin.refreshFailed))
    },
  })

  const leadingBlanks = (getDay(monthDays[0]!) + 6) % 7 // Monday-first

  return (
    <Box data-testid="admin-rate-calendar">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.ratesTitle}
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2, alignItems: 'center' }}>
        <TextField
          select
          size="small"
          label={t.admin.roomType}
          value={effectiveCode}
          onChange={(e) => setRoomTypeCode(e.target.value)}
          sx={{ minWidth: 180 }}
        >
          {(typesQuery.data?.content ?? []).map((t) => (
            <MenuItem key={t.code} value={t.code}>
              {t.code}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          size="small"
          type="month"
          label={t.admin.month}
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        {isAdmin ? (
          <Button
            variant="outlined"
            disabled={refreshMutation.isPending}
            onClick={() => {
              setRefreshMsg(null)
              refreshMutation.mutate()
            }}
            data-testid="refresh-prices"
          >
            {t.admin.refreshPrices}
          </Button>
        ) : null}
      </Box>

      {refreshMsg ? (
        <Alert severity="info" sx={{ mb: 2 }} data-testid="refresh-prices-message">
          {refreshMsg}
        </Alert>
      ) : null}
      {calendarQuery.isFetching ? <PageSkeleton variant="cards" rows={6} /> : null}
      {calendarQuery.isError ? (
        <ProblemAlert
          error={calendarQuery.error}
          fallback={t.admin.ratesError}
          data-testid="rate-calendar-error"
        />
      ) : null}
      {calendarQuery.isSuccess && (calendarQuery.data.days?.length ?? 0) === 0 ? (
        <EmptyState
          title={t.admin.ratesEmptyTitle}
          description={t.admin.ratesEmptyDesc}
          data-testid="rate-calendar-empty"
        />
      ) : null}

      {!calendarQuery.isFetching ? (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(7, 1fr)',
            gap: 1,
          }}
          data-testid="rate-calendar-grid"
        >
          {t.common.weekdays.map((d) => (
            <Typography key={d} variant="caption" sx={{ textAlign: 'center', fontWeight: 600 }}>
              {d}
            </Typography>
          ))}
          {Array.from({ length: leadingBlanks }).map((_, i) => (
            <Box key={`pad-${i}`} />
          ))}
          {monthDays.map((day) => {
            const iso = format(day, 'yyyy-MM-dd')
            const cell = daysByDate.get(iso)
            const price = cell?.price ?? selectedType?.basePrice ?? 0
            const source = cell?.source ?? 'BASE'
            return (
              <Box
                key={iso}
                component="button"
                type="button"
                onClick={() => {
                  if (!isAdmin) {
                    return
                  }
                  setSelected(
                    cell ?? { date: iso, price, source, demandIndicator: 0, fromCalendar: false },
                  )
                  setOverridePrice(String(price))
                  setOverrideError(null)
                }}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  p: 1,
                  textAlign: 'left',
                  bgcolor: heatColor(price, minPrice || price, maxPrice || price),
                  cursor: isAdmin ? 'pointer' : 'default',
                  minHeight: 88,
                  '&:focus-visible': {
                    outline: '3px solid',
                    outlineColor: 'secondary.main',
                    outlineOffset: 2,
                  },
                }}
                data-testid={`rate-cell-${iso}`}
              >
                <Typography variant="caption" sx={{ display: 'block' }}>
                  {format(day, 'd')}
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {formatPln(price)}
                </Typography>
                <RateSourceBadge source={source} />
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                  {t.admin.demand} {cell?.demandIndicator ?? '—'}
                </Typography>
              </Box>
            )
          })}
        </Box>
      ) : null}

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} fullWidth maxWidth="xs">
        <DialogTitle>
          {selected?.date
            ? tf(t.admin.manualOverride, { date: selected.date })
            : t.admin.manualOverride}
        </DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: 1 }}>
          {overrideError ? <Alert severity="error">{overrideError}</Alert> : null}
          <Typography variant="body2" color="text.secondary">
            {t.admin.typeRange}: {formatPln(selectedType?.minPrice ?? 0)} –{' '}
            {formatPln(selectedType?.maxPrice ?? 0)}
          </Typography>
          <TextField
            label={t.admin.pricePln}
            type="number"
            value={overridePrice}
            onChange={(e) => setOverridePrice(e.target.value)}
            data-testid="override-price"
          />
        </DialogContent>
        <DialogActions>
          {selected?.source === 'MANUAL' ? (
            <Button
              color="secondary"
              onClick={() => clearMutation.mutate()}
              disabled={clearMutation.isPending}
            >
              {t.admin.removeOverride}
            </Button>
          ) : null}
          <Button onClick={() => setSelected(null)}>{t.common.cancel}</Button>
          <Button
            variant="contained"
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
          >
            {t.admin.saveManual}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
