package pl.smarthotel.pms.pricing;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.web.ApiPaths;

/**
 * Phase 8 placeholders: browser talks only to pms-core; pricing-service stays private.
 * Returns empty / not-wired responses until the resilient client is plugged in.
 */
@RestController
@RequestMapping(ApiPaths.ADMIN + "/pricing")
@Tag(name = "Admin — Pricing proxies")
@SecurityRequirement(name = BEARER_JWT)
public class PricingProxyController {

    @PostMapping("/refresh")
    @PreAuthorize("hasRole('ADMIN')")
    PricingRefreshResponse refresh() {
        return new PricingRefreshResponse(
                "NOT_WIRED", "Rate-calendar refresh via pricing-service lands in Phase 8", 0);
    }

    @GetMapping("/events")
    @PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
    List<PricingEventResponse> events(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        if (to.isBefore(from)) {
            return List.of();
        }
        return List.of();
    }

    @GetMapping("/demand-indicators")
    @PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
    List<DemandIndicatorPoint> demandIndicators(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        if (to.isBefore(from)) {
            return List.of();
        }
        return List.of();
    }
}
