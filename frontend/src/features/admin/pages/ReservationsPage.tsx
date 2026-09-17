import {
  Box,
  Button,
  Drawer,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import {
  adminKeys,
  fetchReservation,
  fetchReservations,
  reservationAction,
  type AdminReservation,
} from '@/features/admin/api/adminApi'
import { WalkInReservationDialog } from '@/features/admin/components/WalkInReservationDialog'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'
import { formatHotelDateDisplay } from '@/shared/lib/hotelDates'
import { formatPln } from '@/shared/lib/money'

type StatusFilter = '' | 'CONFIRMED' | 'CHECKED_IN' | 'CHECKED_OUT' | 'CANCELLED' | 'NO_SHOW'

const actionsFor: Record<
  NonNullable<AdminReservation['status']>,
  Array<'check-in' | 'check-out' | 'cancel' | 'no-show'>
> = {
  CONFIRMED: ['check-in', 'cancel', 'no-show'],
  CHECKED_IN: ['check-out'],
  CHECKED_OUT: [],
  CANCELLED: [],
  NO_SHOW: [],
}

export function ReservationsPage() {
  const { t } = useI18n()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<StatusFilter>('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [query, setQuery] = useState('')
  const [applied, setApplied] = useState({ status: '', from: '', to: '', query: '' })
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [walkInOpen, setWalkInOpen] = useState(false)

  const listParams = useMemo(
    () => ({
      page: 0,
      size: 50,
      status: applied.status || undefined,
      from: applied.from || undefined,
      to: applied.to || undefined,
      query: applied.query || undefined,
    }),
    [applied],
  )

  const listQuery = useQuery({
    queryKey: adminKeys.reservations(listParams),
    queryFn: () => fetchReservations(listParams),
  })

  const detailQuery = useQuery({
    queryKey: adminKeys.reservation(selectedId ?? 0),
    queryFn: () => fetchReservation(selectedId!),
    enabled: selectedId != null,
  })

  const actionMutation = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number
      action: 'check-in' | 'check-out' | 'cancel' | 'no-show'
    }) => reservationAction(id, action),
    onMutate: async ({ id, action }) => {
      await queryClient.cancelQueries({ queryKey: adminKeys.reservations(listParams) })
      const previous = queryClient.getQueryData(adminKeys.reservations(listParams))
      queryClient.setQueryData(adminKeys.reservations(listParams), (old: unknown) => {
        if (!old || typeof old !== 'object' || !('content' in old)) {
          return old
        }
        const page = old as { content?: AdminReservation[] }
        const nextStatus =
          action === 'check-in'
            ? 'CHECKED_IN'
            : action === 'check-out'
              ? 'CHECKED_OUT'
              : action === 'cancel'
                ? 'CANCELLED'
                : 'NO_SHOW'
        return {
          ...page,
          content: (page.content ?? []).map((row) =>
            row.id === id ? { ...row, status: nextStatus } : row,
          ),
        }
      })
      return { previous }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) {
        queryClient.setQueryData(adminKeys.reservations(listParams), ctx.previous)
      }
    },
    onSettled: async (_data, _err, vars) => {
      await queryClient.invalidateQueries({ queryKey: adminKeys.reservations(listParams) })
      if (vars?.id != null) {
        await queryClient.invalidateQueries({ queryKey: adminKeys.reservation(vars.id) })
      }
    },
  })

  const selectedSummary = (listQuery.data?.content ?? []).find((r) => r.id === selectedId)

  return (
    <Box data-testid="admin-reservations">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.reservationsTitle}
      </Typography>

      <Button
        variant="contained"
        onClick={() => setWalkInOpen(true)}
        sx={{ mb: 2 }}
        data-testid="walk-in-open"
      >
        {t.admin.walkIn}
      </Button>

      <Box
        component="form"
        onSubmit={(e) => {
          e.preventDefault()
          setApplied({ status, from, to, query: query.trim() })
        }}
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: 'repeat(5, 1fr)' },
          mb: 2,
        }}
      >
        <TextField
          select
          size="small"
          label={t.admin.status}
          value={status}
          onChange={(e) => setStatus(e.target.value as StatusFilter)}
        >
          <MenuItem value="">{t.common.all}</MenuItem>
          <MenuItem value="CONFIRMED">{t.status.CONFIRMED}</MenuItem>
          <MenuItem value="CHECKED_IN">{t.status.CHECKED_IN}</MenuItem>
          <MenuItem value="CHECKED_OUT">{t.status.CHECKED_OUT}</MenuItem>
          <MenuItem value="CANCELLED">{t.status.CANCELLED}</MenuItem>
          <MenuItem value="NO_SHOW">{t.status.NO_SHOW}</MenuItem>
        </TextField>
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
        <TextField
          size="small"
          label={t.admin.search}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" variant="contained">
          {t.common.filter}
        </Button>
      </Box>

      {listQuery.isFetching ? <PageSkeleton variant="table" rows={8} /> : null}

      {listQuery.isError ? (
        <ProblemAlert
          error={listQuery.error}
          fallback={t.admin.reservationsError}
          data-testid="reservations-error"
        />
      ) : null}
      {actionMutation.isError ? (
        <Box sx={{ mb: 2 }}>
          <ProblemAlert
            error={actionMutation.error}
            fallback={t.admin.actionError}
            data-testid="reservation-action-error"
          />
        </Box>
      ) : null}

      {listQuery.isSuccess && (listQuery.data.content?.length ?? 0) === 0 ? (
        <EmptyState
          title={t.admin.reservationsEmptyTitle}
          description={t.admin.reservationsEmptyDesc}
          data-testid="reservations-empty"
        />
      ) : null}

      {!listQuery.isFetching && (listQuery.data?.content?.length ?? 0) > 0 ? (
        <Table size="small" data-testid="reservations-table">
          <TableHead>
            <TableRow>
              <TableCell>{t.admin.colCode}</TableCell>
              <TableCell>{t.admin.colGuest}</TableCell>
              <TableCell>{t.admin.colDates}</TableCell>
              <TableCell>{t.admin.colRoom}</TableCell>
              <TableCell>{t.admin.colStatus}</TableCell>
              <TableCell>{t.admin.colAmount}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(listQuery.data?.content ?? []).map((row) => (
              <TableRow
                key={row.id}
                hover
                selected={row.id === selectedId}
                tabIndex={0}
                sx={{ cursor: 'pointer' }}
                onClick={() => setSelectedId(row.id ?? null)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setSelectedId(row.id ?? null)
                  }
                }}
                data-testid={`reservation-row-${row.confirmationCode}`}
              >
                <TableCell>{row.confirmationCode}</TableCell>
                <TableCell>
                  {row.guestName}
                  <Typography variant="caption" sx={{ display: 'block' }} color="text.secondary">
                    {row.guestEmail}
                  </Typography>
                </TableCell>
                <TableCell>
                  {row.checkIn ? formatHotelDateDisplay(row.checkIn) : '—'} →{' '}
                  {row.checkOut ? formatHotelDateDisplay(row.checkOut) : '—'}
                </TableCell>
                <TableCell>
                  {row.roomType} / {row.roomNumber}
                </TableCell>
                <TableCell>{row.status ? t.status[row.status] : row.status}</TableCell>
                <TableCell>{formatPln(row.totalPrice ?? 0)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      <Drawer anchor="right" open={selectedId != null} onClose={() => setSelectedId(null)}>
        <Box sx={{ width: { xs: 320, sm: 400 }, p: 3 }} data-testid="reservation-drawer">
          <Typography variant="h6" gutterBottom>
            {t.admin.detailTitle}
          </Typography>
          {detailQuery.isError ? (
            <ProblemAlert
              error={detailQuery.error}
              fallback={t.admin.detailError}
              data-testid="reservation-detail-error"
            />
          ) : null}
          {selectedSummary ? (
            <Stack spacing={1} sx={{ mb: 2 }}>
              <Typography>
                {t.admin.colCode}: <strong>{selectedSummary.confirmationCode}</strong>
              </Typography>
              <Typography>
                {t.admin.status}:{' '}
                {(() => {
                  const s = detailQuery.data?.status ?? selectedSummary.status
                  return s ? t.status[s] : s
                })()}
              </Typography>
              <Typography>
                {t.admin.colGuest}: {selectedSummary.guestName} ({selectedSummary.guestEmail})
              </Typography>
              <Typography>
                {selectedSummary.roomType} / {selectedSummary.roomNumber}
              </Typography>
              <Typography>
                {t.booking.total}:{' '}
                {formatPln(detailQuery.data?.totalPrice ?? selectedSummary.totalPrice ?? 0)}
              </Typography>
            </Stack>
          ) : null}

          {(detailQuery.data?.priceBreakdown ?? []).length > 0 ? (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2">{t.admin.priceBreakdown}</Typography>
              {(detailQuery.data?.priceBreakdown ?? []).map((line) => (
                <Typography key={line.date} variant="body2">
                  {line.date}: {formatPln(line.price ?? 0)}
                </Typography>
              ))}
            </Box>
          ) : null}

          <Stack spacing={1}>
            {(actionsFor[selectedSummary?.status ?? 'CANCELLED'] ?? []).map((action) => (
              <Button
                key={action}
                variant="outlined"
                disabled={actionMutation.isPending || selectedId == null}
                onClick={() =>
                  selectedId != null && actionMutation.mutate({ id: selectedId, action })
                }
                data-testid={`reservation-action-${action}`}
              >
                {action}
              </Button>
            ))}
          </Stack>
        </Box>
      </Drawer>

      <WalkInReservationDialog
        open={walkInOpen}
        onClose={() => setWalkInOpen(false)}
        listParams={listParams}
      />
    </Box>
  )
}
