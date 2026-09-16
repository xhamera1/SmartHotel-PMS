package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.time.LocalDate;
import pl.smarthotel.pms.ratecalendar.PriceSource;

public record NightAvailability(LocalDate date, BigDecimal bar, PriceSource priceSource) {}
