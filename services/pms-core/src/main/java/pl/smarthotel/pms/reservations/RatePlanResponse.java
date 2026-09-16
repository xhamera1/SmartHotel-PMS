package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;

public record RatePlanResponse(
        Long id,
        String code,
        String name,
        String description,
        boolean refundable,
        boolean breakfastIncluded,
        BigDecimal priceModifier,
        boolean active,
        short sortOrder) {}
