package pl.smarthotel.pms.rooms;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.util.List;

public record UpdateRoomTypeRequest(
        @NotBlank @Size(max = 30) String code,
        @NotBlank @Size(max = 100) String name,
        String description,
        @NotNull @Min(1) @Max(10) Short capacity,
        @NotNull @DecimalMin(value = "0.01") BigDecimal basePrice,
        @NotNull @DecimalMin(value = "0.01") BigDecimal minPrice,
        @NotNull @DecimalMin(value = "0.01") BigDecimal maxPrice,
        List<String> amenities,
        @NotNull Boolean active) {

    @AssertTrue(message = "minPrice must be ≤ basePrice ≤ maxPrice")
    public boolean isValidPriceBand() {
        if (minPrice == null || basePrice == null || maxPrice == null) {
            return true;
        }
        return minPrice.compareTo(basePrice) <= 0 && basePrice.compareTo(maxPrice) <= 0;
    }
}
