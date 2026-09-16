package pl.smarthotel.pms.ratecalendar;

/**
 * Provenance of a nightly BAR on {@code rate_calendar} (or the booking-path fallback).
 */
public enum PriceSource {
    ML_MODEL,
    MANUAL,
    BASE,
    BASE_FALLBACK
}
