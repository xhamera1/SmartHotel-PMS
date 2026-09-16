package pl.smarthotel.pms.ratecalendar;

import java.util.List;

public record RateCalendarResponse(String roomTypeCode, List<RateCalendarDayResponse> days) {}
