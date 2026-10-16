package pl.smarthotel.pms.dashboard;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import pl.smarthotel.pms.common.domain.OccupancyCalculator;

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
        return new DashboardKpisResponse(
                businessDate,
                OccupancyCalculator.rateBigDecimal(occupied, sellable),
                occupied,
                sellable,
                arrivals,
                departures,
                mtdRevenue.setScale(2, RoundingMode.HALF_UP),
                "PLN");
    }
}
