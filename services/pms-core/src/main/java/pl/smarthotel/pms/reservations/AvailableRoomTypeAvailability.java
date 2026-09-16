package pl.smarthotel.pms.reservations;

import java.util.List;

public record AvailableRoomTypeAvailability(
        String code,
        String name,
        short capacity,
        long roomsLeft,
        List<NightAvailability> nights,
        List<RatePlanQuote> ratePlans) {}
