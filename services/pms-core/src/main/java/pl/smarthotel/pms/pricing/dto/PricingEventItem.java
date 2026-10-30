package pl.smarthotel.pms.pricing.dto;

import java.math.BigDecimal;

public record PricingEventItem(
        long id,
        String name,
        String category,
        String startsAt,
        String endsAt,
        Integer impactScore,
        Double distanceKm,
        BigDecimal confidence,
        String rationale) {}
