package pl.smarthotel.pms.dashboard;

import java.time.LocalDate;
import java.util.List;

public record DashboardTimeseriesResponse(
        LocalDate from, LocalDate to, String currency, List<DashboardDayPoint> points) {}
