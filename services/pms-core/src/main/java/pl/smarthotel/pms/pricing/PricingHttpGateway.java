package pl.smarthotel.pms.pricing;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import java.time.LocalDate;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import pl.smarthotel.pms.common.web.CorrelationIds;
import pl.smarthotel.pms.pricing.dto.PricingDemandItem;
import pl.smarthotel.pms.pricing.dto.PricingDemandResponse;
import pl.smarthotel.pms.pricing.dto.PricingEventItem;
import pl.smarthotel.pms.pricing.dto.PricingEventsResponse;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;

/**
 * Low-level HTTP calls decorated with Resilience4j. Exceptions propagate so retry
 * can run; {@link PricingClient} maps failures to empty results.
 *
 * <p>Captures {@code X-Request-ID} from MDC on the calling thread before {@code supplyAsync}
 * so correlation survives the async hop (Phase 10).
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
        String traceId = CorrelationIds.peek();
        return CompletableFuture.supplyAsync(() -> postQuotes(restClient, request, traceId));
    }

    @CircuitBreaker(name = "pricing")
    @TimeLimiter(name = "pricing-on-demand")
    @Retry(name = "pricing")
    public CompletableFuture<PricingQuotesResponse> postQuotesOnDemand(PricingQuotesRequest request) {
        String traceId = CorrelationIds.peek();
        return CompletableFuture.supplyAsync(() -> postQuotes(onDemandRestClient, request, traceId));
    }

    @CircuitBreaker(name = "pricing")
    @Retry(name = "pricing")
    public List<PricingEventItem> getEvents(LocalDate from, LocalDate to) {
        String traceId = CorrelationIds.peek();
        RestClient.RequestHeadersSpec<?> spec = restClient
                .get()
                .uri(uriBuilder -> uriBuilder
                        .path("/api/v1/events")
                        .queryParam("from", from)
                        .queryParam("to", to)
                        .build())
                .accept(MediaType.APPLICATION_JSON);
        applyTrace(spec, traceId);
        PricingEventsResponse response = spec.retrieve().body(PricingEventsResponse.class);
        if (response == null || response.items() == null) {
            return List.of();
        }
        return response.items();
    }

    @CircuitBreaker(name = "pricing")
    @Retry(name = "pricing")
    public List<PricingDemandItem> getDemandIndicators(LocalDate from, LocalDate to) {
        String traceId = CorrelationIds.peek();
        RestClient.RequestHeadersSpec<?> spec = restClient
                .get()
                .uri(uriBuilder -> uriBuilder
                        .path("/api/v1/demand-indicators")
                        .queryParam("from", from)
                        .queryParam("to", to)
                        .build())
                .accept(MediaType.APPLICATION_JSON);
        applyTrace(spec, traceId);
        PricingDemandResponse response = spec.retrieve().body(PricingDemandResponse.class);
        if (response == null || response.items() == null) {
            return List.of();
        }
        return response.items();
    }

    private static PricingQuotesResponse postQuotes(
            RestClient client, PricingQuotesRequest request, String traceId) {
        RestClient.RequestBodySpec spec = client
                .post()
                .uri("/api/v1/quotes")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON);
        if (traceId != null && !traceId.isBlank()) {
            spec = spec.header(CorrelationIds.HEADER, traceId);
        }
        return spec.body(request).retrieve().body(PricingQuotesResponse.class);
    }

    private static void applyTrace(RestClient.RequestHeadersSpec<?> spec, String traceId) {
        if (traceId != null && !traceId.isBlank()) {
            spec.header(CorrelationIds.HEADER, traceId);
        }
    }
}
