import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AdminLoginPage } from '@/features/admin/auth/AdminLoginPage'
import { AdminShell } from '@/features/admin/layout/AdminShell'
import { AdminPlaceholderPage } from '@/features/admin/pages/AdminPlaceholderPage'
import { BookingHomePage } from '@/features/booking/pages/BookingHomePage'
import { BookingSearchPage } from '@/features/booking/pages/BookingSearchPage'
import { ManageBookingPage } from '@/features/booking/pages/ManageBookingPage'
import { RequireAuth } from '@/shared/auth/RequireAuth'
import { RequireRole } from '@/shared/auth/RequireRole'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <BookingHomePage />,
  },
  {
    path: '/booking',
    element: <BookingSearchPage />,
  },
  {
    path: '/booking/manage',
    element: <ManageBookingPage />,
  },
  {
    path: '/admin/login',
    element: <AdminLoginPage />,
  },
  {
    path: '/admin',
    element: <RequireAuth />,
    children: [
      {
        element: <AdminShell />,
        children: [
          {
            index: true,
            element: (
              <AdminPlaceholderPage
                title="Dashboard"
                detail="KPI cards and charts arrive in step 4."
              />
            ),
          },
          {
            path: 'reservations',
            element: (
              <AdminPlaceholderPage
                title="Reservations"
                detail="List, filters, and state actions arrive in step 4."
              />
            ),
          },
          {
            path: 'guests',
            element: (
              <AdminPlaceholderPage title="Guests" detail="Guest search/CRUD arrives in step 4." />
            ),
          },
          {
            element: <RequireRole roles={['ADMIN']} />,
            children: [
              {
                path: 'room-types',
                element: (
                  <AdminPlaceholderPage
                    title="Room types"
                    detail="ADMIN-only room-type CRUD arrives in step 4."
                  />
                ),
              },
              {
                path: 'rooms',
                element: (
                  <AdminPlaceholderPage
                    title="Rooms"
                    detail="ADMIN-only room CRUD arrives in step 4."
                  />
                ),
              },
              {
                path: 'rate-calendar',
                element: (
                  <AdminPlaceholderPage
                    title="Rate calendar"
                    detail="Heatmap + manual overrides arrive in step 4."
                  />
                ),
              },
            ],
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])
