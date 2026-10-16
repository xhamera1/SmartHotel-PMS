package pl.smarthotel.pms.pricing.dto;

import java.time.LocalDate;
import java.util.List;

public record PricingDemandItem(LocalDate date, int indicator, List<Integer> topEventIds) {}
