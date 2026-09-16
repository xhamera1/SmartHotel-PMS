package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.time.LocalDate;

public record RateCalendarDayResponse(
        LocalDate date,
        BigDecimal price,
        PriceSource source,
        Short demandIndicator,
        boolean fromCalendar) {}
