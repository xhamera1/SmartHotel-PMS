package pl.smarthotel.pms.pricing;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PricingEventResponse(
        String id,
        String title,
        LocalDate startDate,
        LocalDate endDate,
        BigDecimal impactScore,
        BigDecimal confidence,
        String rationale,
        String source) {}
