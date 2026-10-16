package pl.smarthotel.pms.pricing.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;

public record PricingQuoteItemResponse(
        String roomTypeCode,
        LocalDate date,
        BigDecimal price,
        double multiplier,
        int demandIndicator,
        Map<String, Object> factors,
        String modelVersion) {}
