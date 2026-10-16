package pl.smarthotel.pms.common.domain;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Single source of truth for the occupancy-rate formula used across the PMS.
 *
 * <p><strong>Occupancy Rate</strong> ({@code 0.0 – 1.0}) is defined as:
 *
 * <pre>   occupancy = occupied / sellable</pre>
 *
 * where
 * <ul>
 *   <li><em>occupied</em> — number of rooms with an active (checked-in or confirmed-future)
 *       reservation that overlaps the given date</li>
 *   <li><em>sellable</em> — total inventory minus OUT_OF_SERVICE rooms</li>
 * </ul>
 *
 * <p>The value is clamped to {@code [0, 1]}. When {@code sellable == 0} the result is {@code 0}
 * (no rooms → no occupancy, prevents division by zero).
 *
 * <h3>Usage contexts</h3>
 * <table>
 *   <tr><th>Caller</th><th>Purpose</th></tr>
 *   <tr><td>{@code DashboardService / DashboardKpisResponse}</td>
 *       <td>Today's KPI card and time-series chart</td></tr>
 *   <tr><td>{@code RateCalendarPriceProvider}</td>
 *       <td>On-demand pricing request to pricing-service</td></tr>
 *   <tr><td>{@code RateCalendarService}</td>
 *       <td>Batch rate-calendar rebuild pricing requests</td></tr>
 * </table>
 *
 * <p>The resulting {@code double} (for pricing features) and {@code BigDecimal} (for JSON
 * responses) are both derived from the same formula to keep the system consistent.
 */
public final class OccupancyCalculator {

    private static final BigDecimal ONE_SCALED = BigDecimal.ONE.setScale(4, RoundingMode.HALF_UP);

    private OccupancyCalculator() {}

    /**
     * Returns occupancy rate as a {@code double} in [0, 1] — used for pricing-service features.
     */
    public static double rate(long occupied, long sellable) {
        if (sellable <= 0) return 0.0;
        return Math.min(1.0, (double) occupied / sellable);
    }

    /**
     * Returns occupancy rate as {@link BigDecimal} with 4 decimal places — used for API responses.
     */
    public static BigDecimal rateBigDecimal(long occupied, long sellable) {
        if (sellable <= 0) {
            return BigDecimal.ZERO.setScale(4, RoundingMode.HALF_UP);
        }
        BigDecimal raw = BigDecimal.valueOf(occupied)
                .divide(BigDecimal.valueOf(sellable), 4, RoundingMode.HALF_UP);
        return raw.compareTo(ONE_SCALED) > 0 ? ONE_SCALED : raw;
    }
}
