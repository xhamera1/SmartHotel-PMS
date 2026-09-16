package pl.smarthotel.pms.rooms;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record UpdateRoomRequest(
        @NotBlank @Size(max = 10) String roomNumber,
        @NotNull Long roomTypeId,
        Short floor,
        @NotNull RoomStatus status,
        String notes) {}
