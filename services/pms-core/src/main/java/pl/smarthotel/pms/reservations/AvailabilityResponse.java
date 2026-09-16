package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import pl.smarthotel.pms.ratecalendar.PriceSource;

public record AvailabilityResponse(
        LocalDate checkIn,
        LocalDate checkOut,
        int guests,
        String currency,
        List<AvailableRoomTypeAvailability> roomTypes) {}
