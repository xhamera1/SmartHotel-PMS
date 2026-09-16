package pl.smarthotel.pms.reservations;

import java.time.LocalDate;
import java.util.List;

public record AvailabilityResponse(
        LocalDate checkIn,
        LocalDate checkOut,
        int guests,
        String currency,
        List<AvailableRoomTypeAvailability> roomTypes) {}
