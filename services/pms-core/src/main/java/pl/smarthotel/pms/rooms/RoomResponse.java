package pl.smarthotel.pms.rooms;

import java.time.Instant;

public record RoomResponse(
        Long id,
        String roomNumber,
        Long roomTypeId,
        String roomTypeCode,
        Short floor,
        RoomStatus status,
        String notes,
        Instant createdAt,
        Instant updatedAt) {}
