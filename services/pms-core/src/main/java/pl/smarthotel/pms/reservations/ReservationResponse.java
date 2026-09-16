package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record ReservationResponse(
        Long id,
        String confirmationCode,
        ReservationStatus status,
        String roomType,
        String roomNumber,
        RatePlanSummary ratePlan,
        LocalDate checkIn,
        LocalDate checkOut,
        short adults,
        BigDecimal totalPrice,
        String currency,
        List<PriceBreakdownLine> priceBreakdown,
        ReservationSource source) {

    public record RatePlanSummary(String code, boolean refundable, boolean breakfastIncluded) {}
}
