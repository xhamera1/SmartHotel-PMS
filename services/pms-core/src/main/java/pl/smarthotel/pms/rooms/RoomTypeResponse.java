package pl.smarthotel.pms.rooms;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

public record RoomTypeResponse(
        Long id,
        String code,
        String name,
        String description,
        short capacity,
        BigDecimal basePrice,
        BigDecimal minPrice,
        BigDecimal maxPrice,
        String currency,
        List<String> amenities,
        boolean active,
        Instant createdAt,
        Instant updatedAt) {}
