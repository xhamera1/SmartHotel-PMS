package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;

public record RatePlanQuote(
        String code,
        String name,
        boolean refundable,
        boolean breakfastIncluded,
        BigDecimal totalPrice) {}
