import { Box, Button, Typography } from '@mui/material'
import { Component, type ErrorInfo, type ReactNode } from 'react'
import { getMessages } from '@/shared/i18n/localeStore'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'
import { testIds } from '@/shared/ui/testids'

type Props = { children: ReactNode; title?: string }
type State = { error: Error | null }

/**
 * Catches render failures and surfaces a problem-detail-style recovery UI.
 * Query/mutation HTTP errors should still use {@link ProblemAlert} inline.
 */
export class AppErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('AppErrorBoundary', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      const t = getMessages()
      return (
        <Box
          data-testid={testIds.appErrorBoundary}
          sx={{ p: 4, maxWidth: 640, mx: 'auto' }}
          role="alert"
        >
          <Typography variant="h5" component="h1" gutterBottom>
            {this.props.title ?? t.common.unexpectedError}
          </Typography>
          <ProblemAlert
            fallback={this.state.error.message || t.common.pageCrashed}
            title={t.common.applicationError}
          />
          <Button
            sx={{ mt: 2 }}
            variant="contained"
            onClick={() => this.setState({ error: null })}
            data-testid="app-error-retry"
          >
            {t.common.tryAgain}
          </Button>
        </Box>
      )
    }
    return this.props.children
  }
}
