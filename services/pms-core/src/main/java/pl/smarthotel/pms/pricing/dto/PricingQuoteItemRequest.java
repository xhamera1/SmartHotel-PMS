package pl.smarthotel.pms.pricing.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PricingQuoteItemRequest(
        String roomTypeCode,
        LocalDate date,
        BigDecimal basePrice,
        BigDecimal minPrice,
        BigDecimal maxPrice,
        double occupancyRate,
        int roomsRemaining,
        int leadTimeDays) {}
