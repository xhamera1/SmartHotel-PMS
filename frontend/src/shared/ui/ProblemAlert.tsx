import { Alert, AlertTitle, Box, Typography } from '@mui/material'
import { getProblemDetail, problemMessage, type ProblemDetail } from '@/shared/api/problem'
import { testIds } from '@/shared/ui/testids'

type ProblemAlertProps = {
  error?: unknown
  problem?: ProblemDetail | null
  fallback?: string
  title?: string
  'data-testid'?: string
}

/** RFC 7807-aware error surface for query/mutation failures and boundaries. */
export function ProblemAlert({
  error,
  problem: problemProp,
  fallback = 'Something went wrong.',
  title,
  'data-testid': dataTestId = testIds.problemAlert,
}: ProblemAlertProps) {
  const problem = problemProp ?? (error != null ? getProblemDetail(error) : null)
  const message = problem
    ? problem.detail || problem.title || fallback
    : error != null
      ? problemMessage(error, fallback)
      : fallback

  return (
    <Alert severity="error" role="alert" data-testid={dataTestId}>
      <AlertTitle>{title ?? problem?.title ?? 'Error'}</AlertTitle>
      <Typography component="p" variant="body2">
        {message}
      </Typography>
      {problem?.status != null || problem?.type || problem?.requestId ? (
        <Box sx={{ mt: 1, typography: 'caption', color: 'text.secondary' }}>
          {problem.status != null ? <div>HTTP {problem.status}</div> : null}
          {problem.type ? <div>type: {problem.type}</div> : null}
          {problem.instance ? <div>instance: {problem.instance}</div> : null}
          {problem.requestId ? <div>requestId: {problem.requestId}</div> : null}
        </Box>
      ) : null}
      {problem?.errors && problem.errors.length > 0 ? (
        <Box component="ul" sx={{ m: 0, pl: 2, mt: 1 }}>
          {problem.errors.map((item, index) => (
            <li key={`${item.field ?? 'field'}-${index}`}>
              {item.field ? `${item.field}: ` : null}
              {item.message}
            </li>
          ))}
        </Box>
      ) : null}
    </Alert>
  )
}
