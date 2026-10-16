package pl.smarthotel.pms.pricing;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import pl.smarthotel.pms.pricing.dto.PricingDemandItem;
import pl.smarthotel.pms.pricing.dto.PricingEventItem;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;

/**
 * Resilient HTTP client for the internal pricing-service (D5).
 * Failures never throw to callers — empty Optional / empty lists instead.
 */
@Component
public class PricingClient {

    private static final Logger log = LoggerFactory.getLogger(PricingClient.class);

    private final PricingHttpGateway gateway;
    private final PricingProperties properties;

    public PricingClient(PricingHttpGateway gateway, PricingProperties properties) {
        this.gateway = gateway;
        this.properties = properties;
    }

    public Optional<PricingQuotesResponse> fetchQuotes(PricingQuotesRequest request) {
        if (!properties.enabled()) {
            return Optional.empty();
        }
        try {
            CompletableFuture<PricingQuotesResponse> future = gateway.postQuotes(request);
            return Optional.ofNullable(future.get());
        } catch (Exception ex) {
            log.warn(
                    "Pricing quotes fallback for {} items: {}",
                    request.items() != null ? request.items().size() : 0,
                    ex.toString());
            return Optional.empty();
        }
    }

    /**
     * On-demand quote with a shorter timeout budget (2 s) for the booking path.
     */
    public Optional<PricingQuotesResponse> fetchQuotesOnDemand(PricingQuotesRequest request) {
        if (!properties.enabled()) {
            return Optional.empty();
        }
        try {
            CompletableFuture<PricingQuotesResponse> future = gateway.postQuotesOnDemand(request);
            return Optional.ofNullable(future.get());
        } catch (Exception ex) {
            log.warn(
                    "On-demand pricing quote fallback for {} items: {}",
                    request.items() != null ? request.items().size() : 0,
                    ex.toString());
            return Optional.empty();
        }
    }

    public List<PricingEventItem> fetchEvents(LocalDate from, LocalDate to) {
        if (!properties.enabled()) {
            return List.of();
        }
        try {
            return gateway.getEvents(from, to);
        } catch (Exception ex) {
            log.warn("Pricing events fallback for {}..{}: {}", from, to, ex.toString());
            return Collections.emptyList();
        }
    }

    public List<PricingDemandItem> fetchDemandIndicators(LocalDate from, LocalDate to) {
        if (!properties.enabled()) {
            return List.of();
        }
        try {
            return gateway.getDemandIndicators(from, to);
        } catch (Exception ex) {
            log.warn("Pricing demand fallback for {}..{}: {}", from, to, ex.toString());
            return Collections.emptyList();
        }
    }
}
