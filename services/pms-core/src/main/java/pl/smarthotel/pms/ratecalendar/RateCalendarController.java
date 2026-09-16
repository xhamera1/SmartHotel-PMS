package pl.smarthotel.pms.ratecalendar;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.web.ApiPaths;

@RestController
@RequestMapping(ApiPaths.ADMIN + "/rate-calendar")
@Tag(name = "Admin — Rate calendar")
@SecurityRequirement(name = BEARER_JWT)
public class RateCalendarController {

    private final RateCalendarService rateCalendarService;

    public RateCalendarController(RateCalendarService rateCalendarService) {
        this.rateCalendarService = rateCalendarService;
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
    RateCalendarResponse get(
            @RequestParam String roomTypeCode,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return rateCalendarService.getCalendar(roomTypeCode, from, to);
    }

    @PutMapping("/{roomTypeCode}/{date}")
    @PreAuthorize("hasRole('ADMIN')")
    RateCalendarDayResponse putManual(
            @PathVariable String roomTypeCode,
            @PathVariable @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date,
            @Valid @RequestBody ManualRateOverrideRequest request) {
        return rateCalendarService.putManualOverride(roomTypeCode, date, request);
    }

    @DeleteMapping("/{roomTypeCode}/{date}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasRole('ADMIN')")
    void deleteManual(
            @PathVariable String roomTypeCode,
            @PathVariable @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        rateCalendarService.deleteManualOverride(roomTypeCode, date);
    }
}
