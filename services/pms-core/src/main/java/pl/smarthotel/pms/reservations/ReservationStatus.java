package pl.smarthotel.pms.reservations;

/**
 * Lifecycle status for reservations. Only {@link #CONFIRMED} and {@link #CHECKED_IN} block
 * inventory (see {@code no_double_booking} exclusion constraint).
 */
public enum ReservationStatus {
    CONFIRMED,
    CHECKED_IN,
    CHECKED_OUT,
    CANCELLED,
    NO_SHOW
}
