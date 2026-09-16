package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.time.LocalDate;

/** Resolved BAR for one hotel night, including whether it came from the calendar or fallback. */
public record NightlyBar(LocalDate date, BigDecimal bar, PriceSource priceSource) {}
