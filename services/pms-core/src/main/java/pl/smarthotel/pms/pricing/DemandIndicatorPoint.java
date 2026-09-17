package pl.smarthotel.pms.pricing;

import java.time.LocalDate;

public record DemandIndicatorPoint(LocalDate date, short demandIndicator) {}
