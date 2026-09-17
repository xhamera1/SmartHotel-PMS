/**
 * E2E `data-testid` convention (Phase 9 / Playwright).
 *
 * Rules:
 * - kebab-case only
 * - feature prefix: `booking-*`, `admin-*`, or a stable flow noun (`search-*`, `guest-*`, …)
 * - dynamic segments after a hyphen: `reservation-row-{code}`, `rate-cell-{yyyy-mm-dd}`
 * - prefer stable semantic names over Polish UI copy
 * - put testids on the interactive control (button/input), not only a wrapper
 *
 * Critical journey anchors (do not rename lightly):
 * - booking-search-form, search-check-in, search-check-out, search-guests, search-submit
 * - availability-results, room-type-card-{code}, select-rate-{room}-{plan}
 * - guest-details-form, mock-payment-authorize, confirm-booking, checkout-error
 * - confirmation-code, go-manage-booking
 * - manage-lookup-form, manage-code, manage-email, cancel-booking
 * - admin-login-form, admin-login-submit
 * - admin-dashboard, admin-reservations, reservation-drawer, reservation-action-{action}
 * - admin-rate-calendar, rate-calendar-grid, rate-cell-{date}, refresh-prices, override-price
 */
export const testIds = {
  skipToContent: 'skip-to-content',
  mainContent: 'main-content',
  appErrorBoundary: 'app-error-boundary',
  problemAlert: 'problem-alert',
  emptyState: 'empty-state',
  loadingSkeleton: 'loading-skeleton',
} as const
