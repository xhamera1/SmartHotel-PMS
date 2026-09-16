package pl.smarthotel.pms.ratecalendar;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record ManualRateOverrideRequest(
        @NotNull @DecimalMin(value = "0.00", inclusive = true) BigDecimal price) {}
