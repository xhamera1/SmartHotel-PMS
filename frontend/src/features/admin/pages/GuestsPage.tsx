import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { adminKeys, fetchGuests } from '@/features/admin/api/adminApi'
import { useI18n } from '@/shared/i18n/useI18n'
import { EmptyState } from '@/shared/ui/EmptyState'
import { PageSkeleton } from '@/shared/ui/PageSkeleton'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

export function GuestsPage() {
  const { t } = useI18n()
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')

  const guestsQuery = useQuery({
    queryKey: adminKeys.guests({ page: 0, size: 50, query: submitted }),
    queryFn: () => fetchGuests({ page: 0, size: 50, query: submitted || undefined }),
  })

  return (
    <Box data-testid="admin-guests">
      <Typography variant="h4" component="h1" gutterBottom>
        {t.admin.guestsTitle}
      </Typography>
      <Box
        component="form"
        onSubmit={(e) => {
          e.preventDefault()
          setSubmitted(query.trim())
        }}
        sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}
      >
        <TextField
          size="small"
          label={t.admin.guestsSearch}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          data-testid="guests-query"
        />
        <Button type="submit" variant="contained">
          {t.common.search}
        </Button>
      </Box>

      {guestsQuery.isFetching ? <PageSkeleton variant="table" rows={6} /> : null}

      {guestsQuery.isError ? (
        <ProblemAlert
          error={guestsQuery.error}
          fallback={t.admin.guestsError}
          data-testid="guests-error"
        />
      ) : null}

      {guestsQuery.isSuccess && (guestsQuery.data.content?.length ?? 0) === 0 ? (
        <EmptyState
          title={t.admin.guestsEmptyTitle}
          description={t.admin.guestsEmptyDesc}
          data-testid="guests-empty"
        />
      ) : null}

      {!guestsQuery.isFetching && (guestsQuery.data?.content?.length ?? 0) > 0 ? (
        <Table size="small" data-testid="guests-table">
          <TableHead>
            <TableRow>
              <TableCell>{t.admin.colName}</TableCell>
              <TableCell>{t.admin.colEmail}</TableCell>
              <TableCell>{t.admin.colPhone}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(guestsQuery.data?.content ?? []).map((g) => (
              <TableRow key={g.id} hover>
                <TableCell>
                  {g.firstName} {g.lastName}
                </TableCell>
                <TableCell>{g.email}</TableCell>
                <TableCell>{g.phone || '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </Box>
  )
}
