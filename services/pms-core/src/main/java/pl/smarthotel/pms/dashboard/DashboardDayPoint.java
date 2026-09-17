package pl.smarthotel.pms.dashboard;

import java.math.BigDecimal;
import java.time.LocalDate;

public record DashboardDayPoint(
        LocalDate date,
        BigDecimal occupancy,
        BigDecimal adr,
        long roomsOccupied,
        long roomsSellable) {}
