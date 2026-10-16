package pl.smarthotel.pms.pricing;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import java.time.LocalDate;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import pl.smarthotel.pms.pricing.dto.PricingDemandItem;
import pl.smarthotel.pms.pricing.dto.PricingDemandResponse;
import pl.smarthotel.pms.pricing.dto.PricingEventItem;
import pl.smarthotel.pms.pricing.dto.PricingEventsResponse;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;

/**
 * Low-level HTTP calls decorated with Resilience4j. Exceptions propagate so retry
 * can run; {@link PricingClient} maps failures to empty results.
 */
@Component
public class PricingHttpGateway {

    private final RestClient restClient;
    private final RestClient onDemandRestClient;

    public PricingHttpGateway(
            @Qualifier("pricingRestClient") RestClient pricingRestClient,
            @Qualifier("pricingOnDemandRestClient") RestClient pricingOnDemandRestClient) {
        this.restClient = pricingRestClient;
        this.onDemandRestClient = pricingOnDemandRestClient;
    }

    @CircuitBreaker(name = "pricing")
    @TimeLimiter(name = "pricing")
    @Retry(name = "pricing")
    public CompletableFuture<PricingQuotesResponse> postQuotes(PricingQuotesRequest request) {
        return CompletableFuture.supplyAsync(() -> restClient
                .post()
                .uri("/api/v1/quotes")
                .body(request)
                .retrieve()
                .body(PricingQuotesResponse.class));
    }

    /**
     * On-demand single-item quote with a shorter timeout budget (2 s) for the
     * booking path (D6). Uses a separate RestClient + TimeLimiter instance.
     */
    @CircuitBreaker(name = "pricing")
    @TimeLimiter(name = "pricing-on-demand")
    @Retry(name = "pricing")
    public CompletableFuture<PricingQuotesResponse> postQuotesOnDemand(PricingQuotesRequest request) {
        return CompletableFuture.supplyAsync(() -> onDemandRestClient
                .post()
                .uri("/api/v1/quotes")
                .body(request)
                .retrieve()
                .body(PricingQuotesResponse.class));
    }

    @CircuitBreaker(name = "pricing")
    @Retry(name = "pricing")
    public List<PricingEventItem> getEvents(LocalDate from, LocalDate to) {
        PricingEventsResponse response = restClient
                .get()
                .uri(uriBuilder -> uriBuilder
                        .path("/api/v1/events")
                        .queryParam("from", from)
                        .queryParam("to", to)
                        .build())
                .retrieve()
                .body(PricingEventsResponse.class);
        if (response == null || response.items() == null) {
            return List.of();
        }
        return response.items();
    }

    @CircuitBreaker(name = "pricing")
    @Retry(name = "pricing")
    public List<PricingDemandItem> getDemandIndicators(LocalDate from, LocalDate to) {
        PricingDemandResponse response = restClient
                .get()
                .uri(uriBuilder -> uriBuilder
                        .path("/api/v1/demand-indicators")
                        .queryParam("from", from)
                        .queryParam("to", to)
                        .build())
                .retrieve()
                .body(PricingDemandResponse.class);
        if (response == null || response.items() == null) {
            return List.of();
        }
        return response.items();
    }
}
