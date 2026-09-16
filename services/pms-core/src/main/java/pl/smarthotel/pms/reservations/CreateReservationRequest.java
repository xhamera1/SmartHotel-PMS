package pl.smarthotel.pms.reservations;

import jakarta.validation.Valid;
import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import pl.smarthotel.pms.guests.GuestUpsertRequest;

public record CreateReservationRequest(
        @NotBlank @Size(max = 30) String roomTypeCode,
        @NotBlank @Size(max = 30) String ratePlanCode,
        @NotNull LocalDate checkIn,
        @NotNull LocalDate checkOut,
        @NotNull @Min(1) @Max(10) Short adults,
        @NotNull @Valid GuestUpsertRequest guest) {

    @AssertTrue(message = "checkOut must be after checkIn")
    public boolean isValidStay() {
        return checkIn == null || checkOut == null || checkOut.isAfter(checkIn);
    }
}
