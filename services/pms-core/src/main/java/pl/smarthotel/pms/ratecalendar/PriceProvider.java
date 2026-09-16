package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/**
 * Pricing seam for the booking path (ADR-0006). Reads precomputed BAR; never calls ML.
 */
public interface PriceProvider {

    /**
     * One {@link NightlyBar} per night in {@code [checkIn, checkOut)}. Missing calendar rows
     * fall back to {@code basePrice} with {@link PriceSource#BASE}.
     */
    List<NightlyBar> resolveBars(
            long roomTypeId, BigDecimal basePrice, LocalDate checkIn, LocalDate checkOut);
}
