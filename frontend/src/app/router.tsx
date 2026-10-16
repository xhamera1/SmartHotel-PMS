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
import { RouteErrorBoundary } from '@/shared/ui/RouteErrorBoundary'

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <RouteErrorBoundary section="booking">
        <BookingHomePage />
      </RouteErrorBoundary>
    ),
  },
  {
    path: '/booking',
    element: (
      <RouteErrorBoundary section="booking">
        <BookingSearchPage />
      </RouteErrorBoundary>
    ),
  },
  {
    path: '/booking/checkout',
    element: (
      <RouteErrorBoundary section="booking">
        <BookingCheckoutPage />
      </RouteErrorBoundary>
    ),
  },
  {
    path: '/booking/confirmation',
    element: (
      <RouteErrorBoundary section="booking">
        <BookingConfirmationPage />
      </RouteErrorBoundary>
    ),
  },
  {
    path: '/booking/manage',
    element: (
      <RouteErrorBoundary section="booking">
        <ManageBookingPage />
      </RouteErrorBoundary>
    ),
  },
  { path: '/admin/login', element: <AdminLoginPage /> },
  {
    path: '/admin',
    element: <RequireAuth />,
    children: [
      {
        element: (
          <RouteErrorBoundary section="admin">
            <AdminShell />
          </RouteErrorBoundary>
        ),
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
