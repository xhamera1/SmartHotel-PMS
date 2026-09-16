import { Container, Typography } from '@mui/material'

export function ManageBookingPage() {
  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography variant="h4" component="h1">
        Manage booking
      </Typography>
      <Typography color="text.secondary">
        Placeholder — lookup and cancel by confirmation code + email arrive in step 3.
      </Typography>
    </Container>
  )
}
