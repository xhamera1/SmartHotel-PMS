package pl.smarthotel.pms.dashboard;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;

public record DashboardKpisResponse(
        LocalDate businessDate,
        BigDecimal occupancyToday,
        long roomsOccupiedToday,
        long roomsSellable,
        long arrivalsToday,
        long departuresToday,
        BigDecimal mtdRevenue,
        String currency) {

    static DashboardKpisResponse of(
            LocalDate businessDate,
            long occupied,
            long sellable,
            long arrivals,
            long departures,
            BigDecimal mtdRevenue) {
        BigDecimal occupancy = sellable == 0
                ? BigDecimal.ZERO.setScale(4, RoundingMode.HALF_UP)
                : BigDecimal.valueOf(occupied)
                        .divide(BigDecimal.valueOf(sellable), 4, RoundingMode.HALF_UP);
        return new DashboardKpisResponse(
                businessDate,
                occupancy,
                occupied,
                sellable,
                arrivals,
                departures,
                mtdRevenue.setScale(2, RoundingMode.HALF_UP),
                "PLN");
    }
}
