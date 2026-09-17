import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AdminLoginPage } from '@/features/admin/auth/AdminLoginPage'
import { AdminShell } from '@/features/admin/layout/AdminShell'
import { DashboardPage } from '@/features/admin/pages/DashboardPage'
import { EventsPage } from '@/features/admin/pages/EventsPage'
import { GuestsPage } from '@/features/admin/pages/GuestsPage'
import { RateCalendarPage } from '@/features/admin/pages/RateCalendarPage'
import { ReservationsPage } from '@/features/admin/pages/ReservationsPage'
import { RoomTypesPage } from '@/features/admin/pages/RoomTypesPage'
import { RoomsPage } from '@/features/admin/pages/RoomsPage'
import { BookingCheckoutPage } from '@/features/booking/pages/BookingCheckoutPage'
import { BookingConfirmationPage } from '@/features/booking/pages/BookingConfirmationPage'
import { BookingHomePage } from '@/features/booking/pages/BookingHomePage'
import { BookingSearchPage } from '@/features/booking/pages/BookingSearchPage'
import { ManageBookingPage } from '@/features/booking/pages/ManageBookingPage'
import { RequireAuth } from '@/shared/auth/RequireAuth'
import { RequireRole } from '@/shared/auth/RequireRole'

export const router = createBrowserRouter([
  { path: '/', element: <BookingHomePage /> },
  { path: '/booking', element: <BookingSearchPage /> },
  { path: '/booking/checkout', element: <BookingCheckoutPage /> },
  { path: '/booking/confirmation', element: <BookingConfirmationPage /> },
  { path: '/booking/manage', element: <ManageBookingPage /> },
  { path: '/admin/login', element: <AdminLoginPage /> },
  {
    path: '/admin',
    element: <RequireAuth />,
    children: [
      {
        element: <AdminShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'reservations', element: <ReservationsPage /> },
          { path: 'guests', element: <GuestsPage /> },
          { path: 'rate-calendar', element: <RateCalendarPage /> },
          { path: 'events', element: <EventsPage /> },
          {
            element: <RequireRole roles={['ADMIN']} />,
            children: [
              { path: 'room-types', element: <RoomTypesPage /> },
              { path: 'rooms', element: <RoomsPage /> },
            ],
          },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
