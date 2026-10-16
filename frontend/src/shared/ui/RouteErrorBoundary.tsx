import { Box, Button, Typography } from '@mui/material'
import { Component, type ErrorInfo, type ReactNode } from 'react'
import { getMessages } from '@/shared/i18n/localeStore'
import { ProblemAlert } from '@/shared/ui/ProblemAlert'

type Props = { children: ReactNode; section?: string }
type State = { error: Error | null }

/**
 * Per-route error boundary that isolates crashes to a section of the app
 * (booking flow or admin panel) instead of taking down the entire UI.
 */
export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(
      `RouteErrorBoundary [${this.props.section ?? 'unknown'}]`,
      error,
      info.componentStack,
    )
  }

  render() {
    if (this.state.error) {
      const t = getMessages()
      return (
        <Box
          data-testid={`route-error-boundary-${this.props.section ?? 'default'}`}
          sx={{ p: 4, maxWidth: 640, mx: 'auto' }}
          role="alert"
        >
          <Typography variant="h5" component="h1" gutterBottom>
            {t.common.unexpectedError}
          </Typography>
          <ProblemAlert
            fallback={this.state.error.message || t.common.pageCrashed}
            title={
              this.props.section ? `Error in ${this.props.section}` : t.common.applicationError
            }
          />
          <Button sx={{ mt: 2 }} variant="contained" onClick={() => this.setState({ error: null })}>
            {t.common.tryAgain}
          </Button>
        </Box>
      )
    }
    return this.props.children
  }
}
