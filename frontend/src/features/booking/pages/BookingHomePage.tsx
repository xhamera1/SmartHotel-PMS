import { Box, Container, Typography } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

export function BookingHomePage() {
  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Typography variant="h2" component="h1" gutterBottom>
        SmartHotel
      </Typography>
      <Typography color="text.secondary" component="p" sx={{ mb: 2 }}>
        Public booking flow scaffold — search, quote, and manage-by-code land in step 3.
      </Typography>
      <Box component="nav" aria-label="Booking shortcuts" sx={{ display: 'flex', gap: 2 }}>
        <RouterLink to="/booking">Start booking</RouterLink>
        <RouterLink to="/booking/manage">Manage booking</RouterLink>
        <RouterLink to="/admin/login">Staff login</RouterLink>
      </Box>
    </Container>
  )
}
