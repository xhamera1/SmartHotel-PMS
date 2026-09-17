import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { adminKeys, fetchDemandIndicators, fetchEvents } from '@/features/admin/api/adminApi'
import { useI18n } from '@/shared/i18n/useI18n'
import { addHotelDays, formatHotelDateDisplay, todayHotelDate } from '@/shared/lib/hotelDates'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

export function EventsPage() {
  const { t } = useI18n()
  const today = todayHotelDate()
  const [from, setFrom] = useState(today)
  const [to, setTo] = useState(addHotelDays(today, 60))

  const eventsQuery = useQuery({
    queryKey: adminKeys.events(from, to),
    queryFn: () => fetchEvents(from, to),
  })
  const demandQuery = useQuery({
    queryKey: adminKeys.demand(from, to),
    queryFn: () => fetchDemandIndicators(from, to),
  })

  const chartData = useMemo(
    () =>
      (demandQuery.data ?? []).map((p) => ({
        date: p.date ?? '',
        demand: p.demandIndicator ?? 0,
      })),
    [demandQuery.data],
  )

  return (
    <Box data-testid="admin-events">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.eventsTitle}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        {t.admin.eventsSubtitle}
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          type="date"
          label={t.common.from}
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <TextField
          size="small"
          type="date"
          label={t.common.to}
          value={to}
          onChange={(e) => setTo(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
      </Box>

      {eventsQuery.isError ? (
        <ProblemAlert
          error={eventsQuery.error}
          fallback={t.admin.eventsError}
          data-testid="events-error"
        />
      ) : null}

      <Typography variant="h6" gutterBottom>
        {t.admin.eventsTitle}
      </Typography>
      {eventsQuery.isFetching ? <PageSkeleton variant="table" rows={4} /> : null}
      {!eventsQuery.isFetching ? (
        <Table size="small" sx={{ mb: 4 }} data-testid="events-table">
          <TableHead>
            <TableRow>
              <TableCell>{t.admin.colEvent}</TableCell>
              <TableCell>{t.admin.colDates}</TableCell>
              <TableCell>{t.admin.colImpact}</TableCell>
              <TableCell>{t.admin.colConfidence}</TableCell>
              <TableCell>{t.admin.colRationale}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(eventsQuery.data ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={5}>
                  <EmptyState
                    title={t.admin.eventsEmptyTitle}
                    description={t.admin.eventsEmptyDesc}
                    data-testid="events-empty"
                  />
                </TableCell>
              </TableRow>
            ) : (
              (eventsQuery.data ?? []).map((ev) => (
                <TableRow key={ev.id}>
                  <TableCell>{ev.title}</TableCell>
                  <TableCell>
                    {ev.startDate ? formatHotelDateDisplay(ev.startDate) : '—'} →{' '}
                    {ev.endDate ? formatHotelDateDisplay(ev.endDate) : '—'}
                  </TableCell>
                  <TableCell>{ev.impactScore ?? '—'}</TableCell>
                  <TableCell>{ev.confidence ?? '—'}</TableCell>
                  <TableCell>{ev.rationale ?? '—'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      ) : null}

      <Typography variant="h6" gutterBottom>
        {t.admin.demandTitle}
      </Typography>
      {demandQuery.isFetching ? <PageSkeleton variant="chart" /> : null}
      {demandQuery.isError ? (
        <ProblemAlert
          error={demandQuery.error}
          fallback={t.admin.demandError}
          data-testid="demand-error"
        />
      ) : null}
      <Box
        sx={{ width: '100%', height: 280, bgcolor: 'background.paper', borderRadius: 2, p: 1 }}
        data-testid="demand-timeline-chart"
      >
        {!demandQuery.isFetching && chartData.length === 0 ? (
          <EmptyState
            title={t.admin.demandEmpty}
            description={t.admin.eventsEmptyDesc}
            data-testid="demand-empty"
          />
        ) : null}
        {chartData.length > 0 ? (
          <ResponsiveContainer>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" minTickGap={24} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Area type="monotone" dataKey="demand" stroke="#0F5C5C" fill="#0F5C5C55" />
            </AreaChart>
          </ResponsiveContainer>
        ) : null}
      </Box>
    </Box>
  )
}
