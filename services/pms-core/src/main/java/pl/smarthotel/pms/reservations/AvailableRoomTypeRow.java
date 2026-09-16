package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;

/** Projection of free inventory grouped by room type for a stay window. */
public record AvailableRoomTypeRow(
        Long roomTypeId,
        String code,
        String name,
        short capacity,
        BigDecimal basePrice,
        long roomsLeft) {}
