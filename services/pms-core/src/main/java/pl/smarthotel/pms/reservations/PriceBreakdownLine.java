package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.time.LocalDate;
import pl.smarthotel.pms.ratecalendar.PriceSource;

/** One night in a reservation's immutable {@code price_breakdown} snapshot. */
public record PriceBreakdownLine(
        LocalDate date, BigDecimal price, BigDecimal barPrice, PriceSource priceSource) {}
