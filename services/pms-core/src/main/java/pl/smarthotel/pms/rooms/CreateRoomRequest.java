package pl.smarthotel.pms.rooms;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateRoomRequest(
        @NotBlank @Size(max = 10) String roomNumber,
        @NotNull Long roomTypeId,
        Short floor,
        RoomStatus status,
        String notes) {}
