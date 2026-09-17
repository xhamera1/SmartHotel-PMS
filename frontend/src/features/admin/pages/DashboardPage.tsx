import { Box, Card, CardContent, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { adminKeys, fetchKpis, fetchTimeseries } from '@/features/admin/api/adminApi'
import { useI18n } from '@/shared/i18n/useI18n'
import { formatHotelDateDisplay } from '@/shared/lib/hotelDates'
import { formatPln } from '@/shared/lib/money'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

export function DashboardPage() {
  const { t, tf } = useI18n()
  const kpisQuery = useQuery({ queryKey: adminKeys.kpis, queryFn: fetchKpis })
  const seriesQuery = useQuery({
    queryKey: adminKeys.timeseries(30),
    queryFn: () => fetchTimeseries(30),
  })

  const kpis = kpisQuery.data
  const chartData =
    seriesQuery.data?.points?.map((p) => ({
      date: p.date ?? '',
      occupancyPct: Math.round((p.occupancy ?? 0) * 1000) / 10,
      adr: p.adr ?? 0,
    })) ?? []

  const subtitleDate = kpis?.businessDate ? ` (${formatHotelDateDisplay(kpis.businessDate)})` : ''

  return (
    <Box data-testid="admin-dashboard">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.dashboardTitle}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {tf(t.admin.dashboardSubtitle, { date: subtitleDate })}
      </Typography>

      {kpisQuery.isLoading ? <PageSkeleton variant="cards" rows={4} /> : null}
      {kpisQuery.isError ? (
        <ProblemAlert
          error={kpisQuery.error}
          fallback={t.admin.kpisError}
          data-testid="dashboard-kpis-error"
        />
      ) : null}

      {kpis ? (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' },
            mb: 4,
          }}
        >
          <KpiCard
            testId="kpi-occupancy"
            label={t.admin.occupancyToday}
            value={`${((kpis.occupancyToday ?? 0) * 100).toFixed(1)}%`}
            hint={tf(t.admin.roomsHint, {
              occupied: kpis.roomsOccupiedToday ?? 0,
              sellable: kpis.roomsSellable ?? 0,
            })}
          />
          <KpiCard
            testId="kpi-arrivals"
            label={t.admin.arrivals}
            value={String(kpis.arrivalsToday ?? 0)}
          />
          <KpiCard
            testId="kpi-departures"
            label={t.admin.departures}
            value={String(kpis.departuresToday ?? 0)}
          />
          <KpiCard
            testId="kpi-mtd-revenue"
            label={t.admin.mtdRevenue}
            value={formatPln(kpis.mtdRevenue ?? 0)}
          />
        </Box>
      ) : null}

      <Card variant="outlined" data-testid="dashboard-chart-card">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t.admin.chartTitle}
          </Typography>
          {seriesQuery.isLoading ? <PageSkeleton variant="chart" /> : null}
          {seriesQuery.isError ? (
            <ProblemAlert
              error={seriesQuery.error}
              fallback={t.admin.chartError}
              data-testid="dashboard-chart-error"
            />
          ) : null}
          {seriesQuery.isSuccess && chartData.length === 0 ? (
            <EmptyState title={t.admin.chartEmptyTitle} description={t.admin.chartEmptyDesc} />
          ) : null}
          {chartData.length > 0 ? (
            <Box sx={{ width: '100%', height: 320 }} data-testid="dashboard-occupancy-adr-chart">
              <ResponsiveContainer>
                <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
                  <YAxis
                    yAxisId="occ"
                    domain={[0, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                    width={48}
                  />
                  <YAxis
                    yAxisId="adr"
                    orientation="right"
                    tickFormatter={(v: number) => `${Math.round(v)}`}
                    width={48}
                  />
                  <Tooltip
                    formatter={(value, name) => {
                      const n = typeof value === 'number' ? value : Number(value)
                      if (name === 'occupancyPct') {
                        return [`${n}%`, t.admin.occupancy]
                      }
                      return [formatPln(n), t.admin.adr]
                    }}
                  />
                  <Legend />
                  <Line
                    yAxisId="occ"
                    type="monotone"
                    dataKey="occupancyPct"
                    name={t.admin.occupancyPct}
                    stroke="#0F5C5C"
                    dot={false}
                    strokeWidth={2}
                  />
                  <Line
                    yAxisId="adr"
                    type="monotone"
                    dataKey="adr"
                    name={t.admin.adrPln}
                    stroke="#C45C26"
                    dot={false}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          ) : null}
        </CardContent>
      </Card>
    </Box>
  )
}

function KpiCard({
  label,
  value,
  hint,
  testId,
}: {
  label: string
  value: string
  hint?: string
  testId: string
}) {
  return (
    <Card variant="outlined" data-testid={testId}>
      <CardContent>
        <Typography color="text.secondary" variant="body2">
          {label}
        </Typography>
        <Typography variant="h4" component="p" sx={{ mt: 1 }}>
          {value}
        </Typography>
        {hint ? (
          <Typography variant="caption" color="text.secondary">
            {hint}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  )
}
