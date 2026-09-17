import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Switch,
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
  createRoomType,
  deleteRoomType,
  fetchRoomTypes,
  updateRoomType,
  type RoomType,
} from '@/features/admin/api/adminApi'
import { problemMessage } from '@/shared/api/problem'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'
import { formatPln } from '@/shared/lib/money'

const emptyForm = {
  code: '',
  name: '',
  description: '',
  capacity: 2,
  basePrice: 400,
  minPrice: 200,
  maxPrice: 800,
  amenities: '',
  active: true,
}

export function RoomTypesPage() {
  const { t } = useI18n()
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<RoomType | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState<string | null>(null)

  const listQuery = useQuery({
    queryKey: adminKeys.roomTypes({ page: 0, size: 50, query }),
    queryFn: () => fetchRoomTypes({ page: 0, size: 50, query: query || undefined }),
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      const amenities = form.amenities
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      if (form.minPrice > form.basePrice || form.basePrice > form.maxPrice) {
        throw new Error(t.validation.priceBand)
      }
      if (editing?.id != null) {
        return updateRoomType(editing.id, {
          code: form.code,
          name: form.name,
          description: form.description || undefined,
          capacity: form.capacity,
          basePrice: form.basePrice,
          minPrice: form.minPrice,
          maxPrice: form.maxPrice,
          amenities,
          active: form.active,
        })
      }
      return createRoomType({
        code: form.code,
        name: form.name,
        description: form.description || undefined,
        capacity: form.capacity,
        basePrice: form.basePrice,
        minPrice: form.minPrice,
        maxPrice: form.maxPrice,
        amenities,
        active: form.active,
      })
    },
    onSuccess: async () => {
      setDialogOpen(false)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'room-types'] })
    },
    onError: (error) => {
      setFormError(
        error instanceof Error ? error.message : problemMessage(error, t.admin.saveFailed),
      )
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteRoomType(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'room-types'] })
    },
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(row: RoomType) {
    setEditing(row)
    setForm({
      code: row.code ?? '',
      name: row.name ?? '',
      description: row.description ?? '',
      capacity: row.capacity ?? 2,
      basePrice: row.basePrice ?? 0,
      minPrice: row.minPrice ?? 0,
      maxPrice: row.maxPrice ?? 0,
      amenities: (row.amenities ?? []).join(', '),
      active: row.active ?? true,
    })
    setFormError(null)
    setDialogOpen(true)
  }

  return (
    <Box data-testid="admin-room-types">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.roomTypesTitle}
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          label={t.admin.search}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="contained" onClick={openCreate} data-testid="room-type-create">
          {t.admin.addRoomType}
        </Button>
      </Box>

      {listQuery.isFetching ? <PageSkeleton variant="table" rows={5} /> : null}
      {listQuery.isError ? (
        <ProblemAlert
          error={listQuery.error}
          fallback={t.admin.saveFailed}
          data-testid="room-types-error"
        />
      ) : null}
      {listQuery.isSuccess && (listQuery.data.content?.length ?? 0) === 0 ? (
        <EmptyState
          title={t.admin.roomTypesTitle}
          description={t.admin.addRoomType}
          data-testid="room-types-empty"
        />
      ) : null}

      {!listQuery.isFetching && (listQuery.data?.content?.length ?? 0) > 0 ? (
        <Table size="small" data-testid="room-types-table">
          <TableHead>
            <TableRow>
              <TableCell>{t.admin.code}</TableCell>
              <TableCell>{t.admin.name}</TableCell>
              <TableCell>{t.admin.capacity}</TableCell>
              <TableCell>{t.admin.basePrice}</TableCell>
              <TableCell>{t.admin.active}</TableCell>
              <TableCell align="right">{t.admin.edit}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(listQuery.data?.content ?? []).map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{row.code}</TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell>{row.capacity}</TableCell>
                <TableCell>
                  {formatPln(row.minPrice ?? 0)} – {formatPln(row.basePrice ?? 0)} –{' '}
                  {formatPln(row.maxPrice ?? 0)}
                </TableCell>
                <TableCell>{row.active ? t.admin.active : '—'}</TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => openEdit(row)}>
                    {t.admin.edit}
                  </Button>
                  <Button
                    size="small"
                    color="secondary"
                    disabled={row.id == null || deleteMutation.isPending}
                    onClick={() => {
                      if (row.id != null && window.confirm(`${t.admin.delete} ${row.code}?`)) {
                        deleteMutation.mutate(row.id)
                      }
                    }}
                  >
                    {t.admin.delete}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? t.admin.edit : t.admin.addRoomType}</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: 1 }}>
          {formError ? <Alert severity="error">{formError}</Alert> : null}
          <TextField
            label={t.admin.code}
            value={form.code}
            onChange={(e) => setForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
            required
          />
          <TextField
            label={t.admin.name}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
          <TextField
            label={t.admin.notes}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            multiline
            minRows={2}
          />
          <TextField
            label={t.admin.capacity}
            type="number"
            value={form.capacity}
            onChange={(e) => setForm((f) => ({ ...f, capacity: Number(e.target.value) }))}
          />
          <TextField
            label={t.admin.minPrice}
            type="number"
            value={form.minPrice}
            onChange={(e) => setForm((f) => ({ ...f, minPrice: Number(e.target.value) }))}
          />
          <TextField
            label={t.admin.basePrice}
            type="number"
            value={form.basePrice}
            onChange={(e) => setForm((f) => ({ ...f, basePrice: Number(e.target.value) }))}
          />
          <TextField
            label={t.admin.maxPrice}
            type="number"
            value={form.maxPrice}
            onChange={(e) => setForm((f) => ({ ...f, maxPrice: Number(e.target.value) }))}
          />
          <TextField
            label={t.admin.amenities}
            value={form.amenities}
            onChange={(e) => setForm((f) => ({ ...f, amenities: e.target.value }))}
          />
          <FormControlLabel
            control={
              <Switch
                checked={form.active}
                onChange={(e) => setForm((f) => ({ ...f, active: e.target.checked }))}
              />
            }
            label={t.admin.active}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t.common.cancel}</Button>
          <Button
            variant="contained"
            disabled={saveMutation.isPending}
            onClick={() => {
              setFormError(null)
              saveMutation.mutate()
            }}
          >
            {t.common.save}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
