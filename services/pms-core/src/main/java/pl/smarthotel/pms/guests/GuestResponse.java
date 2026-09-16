package pl.smarthotel.pms.guests;

import java.time.Instant;

public record GuestResponse(
        Long id,
        String firstName,
        String lastName,
        String email,
        String phone,
        Instant createdAt,
        Instant updatedAt) {}
