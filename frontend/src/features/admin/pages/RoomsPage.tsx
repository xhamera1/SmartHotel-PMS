import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  adminKeys,
  createRoom,
  fetchRoomTypes,
  fetchRooms,
  updateRoom,
  type Room,
} from '@/features/admin/api/adminApi'
import { problemMessage } from '@/shared/api/problem'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

const emptyForm = {
  roomNumber: '',
  roomTypeId: 0,
  floor: 1,
  status: 'AVAILABLE' as 'AVAILABLE' | 'OUT_OF_SERVICE',
  notes: '',
}

export function RoomsPage() {
  const { t } = useI18n()
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Room | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState<string | null>(null)

  const typesQuery = useQuery({
    queryKey: adminKeys.roomTypes({ page: 0, size: 100 }),
    queryFn: () => fetchRoomTypes({ page: 0, size: 100 }),
  })
  const roomsQuery = useQuery({
    queryKey: adminKeys.rooms({ page: 0, size: 100 }),
    queryFn: () => fetchRooms({ page: 0, size: 100 }),
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!form.roomTypeId) {
        throw new Error(t.validation.pickRoomType)
      }
      if (editing?.id != null) {
        return updateRoom(editing.id, {
          roomNumber: form.roomNumber,
          roomTypeId: form.roomTypeId,
          floor: form.floor,
          status: form.status,
          notes: form.notes || undefined,
        })
      }
      return createRoom({
        roomNumber: form.roomNumber,
        roomTypeId: form.roomTypeId,
        floor: form.floor,
        status: form.status,
        notes: form.notes || undefined,
      })
    },
    onSuccess: async () => {
      setDialogOpen(false)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'rooms'] })
    },
    onError: (error) => {
      setFormError(
        error instanceof Error ? error.message : problemMessage(error, t.admin.saveFailed),
      )
    },
  })

  function openCreate() {
    const firstType = typesQuery.data?.content?.[0]?.id ?? 0
    setEditing(null)
    setForm({ ...emptyForm, roomTypeId: firstType })
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(row: Room) {
    setEditing(row)
    setForm({
      roomNumber: row.roomNumber ?? '',
      roomTypeId: row.roomTypeId ?? 0,
      floor: row.floor ?? 1,
      status: row.status ?? 'AVAILABLE',
      notes: row.notes ?? '',
    })
    setFormError(null)
    setDialogOpen(true)
  }

  return (
    <Box data-testid="admin-rooms">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.roomsTitle}
      </Typography>
      <Button variant="contained" onClick={openCreate} sx={{ mb: 2 }} data-testid="room-create">
        {t.admin.addRoom}
      </Button>

      {roomsQuery.isFetching ? <PageSkeleton variant="table" rows={5} /> : null}
      {roomsQuery.isError ? (
        <ProblemAlert
          error={roomsQuery.error}
          fallback={t.admin.saveFailed}
          data-testid="rooms-error"
        />
      ) : null}
      {roomsQuery.isSuccess && (roomsQuery.data.content?.length ?? 0) === 0 ? (
        <EmptyState
          title={t.admin.roomsTitle}
          description={t.admin.addRoom}
          data-testid="rooms-empty"
        />
      ) : null}

      {!roomsQuery.isFetching && (roomsQuery.data?.content?.length ?? 0) > 0 ? (
        <Table size="small" data-testid="rooms-table">
          <TableHead>
            <TableRow>
              <TableCell>{t.admin.roomNumber}</TableCell>
              <TableCell>{t.admin.roomType}</TableCell>
              <TableCell>{t.admin.floor}</TableCell>
              <TableCell>{t.admin.roomStatus}</TableCell>
              <TableCell align="right">{t.admin.edit}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(roomsQuery.data?.content ?? []).map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{row.roomNumber}</TableCell>
                <TableCell>{row.roomTypeCode}</TableCell>
                <TableCell>{row.floor}</TableCell>
                <TableCell>
                  {row.status === 'AVAILABLE'
                    ? t.admin.available
                    : row.status === 'OUT_OF_SERVICE'
                      ? t.admin.outOfService
                      : row.status}
                </TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => openEdit(row)}>
                    {t.admin.edit}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? t.admin.edit : t.admin.addRoom}</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: 1 }}>
          {formError ? <Alert severity="error">{formError}</Alert> : null}
          <TextField
            label={t.admin.roomNumber}
            value={form.roomNumber}
            onChange={(e) => setForm((f) => ({ ...f, roomNumber: e.target.value }))}
            required
          />
          <TextField
            select
            label={t.admin.roomType}
            value={form.roomTypeId}
            onChange={(e) => setForm((f) => ({ ...f, roomTypeId: Number(e.target.value) }))}
          >
            {(typesQuery.data?.content ?? []).map((t) => (
              <MenuItem key={t.id} value={t.id}>
                {t.code} — {t.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label={t.admin.floor}
            type="number"
            value={form.floor}
            onChange={(e) => setForm((f) => ({ ...f, floor: Number(e.target.value) }))}
          />
          <TextField
            select
            label={t.admin.roomStatus}
            value={form.status}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                status: e.target.value as 'AVAILABLE' | 'OUT_OF_SERVICE',
              }))
            }
          >
            <MenuItem value="AVAILABLE">{t.admin.available}</MenuItem>
            <MenuItem value="OUT_OF_SERVICE">{t.admin.outOfService}</MenuItem>
          </TextField>
          <TextField
            label={t.admin.notes}
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            multiline
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t.common.cancel}</Button>
          <Button
            variant="contained"
            disabled={saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {t.common.save}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
