package pl.smarthotel.pms.pricing;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.web.ApiPaths;
import pl.smarthotel.pms.pricing.dto.PricingDemandItem;
import pl.smarthotel.pms.pricing.dto.PricingEventItem;
import pl.smarthotel.pms.ratecalendar.RateCalendarService;

/**
 * Browser talks only to pms-core; pricing-service stays private (Phase 8).
 */
@RestController
@RequestMapping(ApiPaths.ADMIN + "/pricing")
@Tag(name = "Admin — Pricing proxies")
@SecurityRequirement(name = BEARER_JWT)
public class PricingProxyController {

    private final RateCalendarService rateCalendarService;
    private final PricingClient pricingClient;
    private final PricingProperties pricingProperties;

    public PricingProxyController(
            RateCalendarService rateCalendarService,
            PricingClient pricingClient,
            PricingProperties pricingProperties) {
        this.rateCalendarService = rateCalendarService;
        this.pricingClient = pricingClient;
        this.pricingProperties = pricingProperties;
    }

    @PostMapping("/refresh")
    @PreAuthorize("hasRole('ADMIN')")
    PricingRefreshResponse refresh() {
        if (!pricingProperties.enabled()) {
            return new PricingRefreshResponse(
                    "DISABLED", "Pricing integration is disabled (app.pricing.enabled=false)", 0);
        }
        int daysUpdated = rateCalendarService.refreshFromPricing();
        return new PricingRefreshResponse(
                "OK", "Rate calendar refreshed from pricing-service", daysUpdated);
    }

    @GetMapping("/events")
    @PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
    @Cacheable(cacheNames = "pricingEvents", key = "#from.toString() + '-' + #to.toString()")
    public List<PricingEventResponse> events(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        if (to.isBefore(from) || !pricingProperties.enabled()) {
            return List.of();
        }
        return pricingClient.fetchEvents(from, to).stream().map(this::toEventResponse).toList();
    }

    @GetMapping("/demand-indicators")
    @PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
    @Cacheable(cacheNames = "pricingDemand", key = "#from.toString() + '-' + #to.toString()")
    public List<DemandIndicatorPoint> demandIndicators(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        if (to.isBefore(from) || !pricingProperties.enabled()) {
            return List.of();
        }
        return pricingClient.fetchDemandIndicators(from, to).stream()
                .map(this::toDemandPoint)
                .toList();
    }

    private PricingEventResponse toEventResponse(PricingEventItem item) {
        LocalDate start = parseDate(item.startsAt());
        LocalDate end = item.endsAt() != null ? parseDate(item.endsAt()) : start;
        BigDecimal impact =
                item.impactScore() == null ? null : BigDecimal.valueOf(item.impactScore());
        return new PricingEventResponse(
                String.valueOf(item.id()),
                item.name(),
                start,
                end,
                impact,
                null,
                null,
                "pricing-service");
    }

    private DemandIndicatorPoint toDemandPoint(PricingDemandItem item) {
        return new DemandIndicatorPoint(item.date(), (short) Math.max(0, Math.min(100, item.indicator())));
    }

    private static LocalDate parseDate(String iso) {
        if (iso == null || iso.isBlank()) {
            return LocalDate.EPOCH;
        }
        try {
            if (iso.length() > 10) {
                return OffsetDateTime.parse(iso).toLocalDate();
            }
            return LocalDate.parse(iso.substring(0, 10));
        } catch (Exception ex) {
            return LocalDate.EPOCH;
        }
    }
}
