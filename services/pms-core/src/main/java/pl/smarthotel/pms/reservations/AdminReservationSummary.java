package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.time.LocalDate;

/** Compact admin list row (guest identity included for front-desk search). */
public record AdminReservationSummary(
        Long id,
        String confirmationCode,
        ReservationStatus status,
        String roomType,
        String roomNumber,
        String guestName,
        String guestEmail,
        LocalDate checkIn,
        LocalDate checkOut,
        short adults,
        BigDecimal totalPrice,
        String currency,
        ReservationSource source) {}
