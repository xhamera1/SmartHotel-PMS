package pl.smarthotel.pms.pricing;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.equalTo;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.postRequestedFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;

@SpringBootTest(
        classes = PricingClientWireMockTest.TestApplication.class,
        webEnvironment = SpringBootTest.WebEnvironment.NONE)
class PricingClientWireMockTest {

    @RegisterExtension
    static WireMockExtension wireMock =
            WireMockExtension.newInstance().options(wireMockConfig().dynamicPort()).build();

    @DynamicPropertySource
    static void pricingProps(DynamicPropertyRegistry registry) {
        registry.add("app.pricing.enabled", () -> "true");
        registry.add("app.pricing.base-url", wireMock::baseUrl);
        registry.add("app.pricing.api-key", () -> "wiremock-key");
        registry.add("app.pricing.connect-timeout-ms", () -> "500");
        registry.add("app.pricing.read-timeout-ms", () -> "800");
        registry.add("app.pricing.batch-read-timeout-ms", () -> "800");
        registry.add("resilience4j.retry.instances.pricing.max-attempts", () -> "3");
        registry.add("resilience4j.retry.instances.pricing.wait-duration", () -> "50ms");
        registry.add("resilience4j.retry.instances.pricing.enable-exponential-backoff", () -> "false");
        registry.add("resilience4j.circuitbreaker.instances.pricing.sliding-window-size", () -> "6");
        registry.add("resilience4j.circuitbreaker.instances.pricing.minimum-number-of-calls", () -> "6");
        registry.add("resilience4j.circuitbreaker.instances.pricing.failure-rate-threshold", () -> "50");
        registry.add(
                "resilience4j.circuitbreaker.instances.pricing.wait-duration-in-open-state", () -> "5s");
        registry.add(
                "resilience4j.circuitbreaker.instances.pricing.automatic-transition-from-open-to-half-open-enabled",
                () -> "true");
    }

    @Autowired
    private PricingClient pricingClient;

    @Autowired
    private CircuitBreakerRegistry circuitBreakerRegistry;

    @BeforeEach
    void resetCircuitBreaker() {
        CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("pricing");
        cb.reset();
        wireMock.resetRequests();
    }

    @Test
    void shouldParseSuccessfulQuotesResponse() {
        wireMock.stubFor(post(urlEqualTo("/api/v1/quotes"))
                .withHeader("X-Internal-Api-Key", equalTo("wiremock-key"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody(quotesJson("STD", "2026-11-01", "512.50"))));

        Optional<PricingQuotesResponse> response = pricingClient.fetchQuotes(sampleRequest());

        assertThat(response).isPresent();
        assertThat(response.get().modelVersion()).isEqualTo("fixture-v1");
        assertThat(response.get().items()).hasSize(1);
        assertThat(response.get().items().getFirst().price()).isEqualByComparingTo("512.50");
        assertThat(response.get().items().getFirst().demandIndicator()).isEqualTo(42);
    }

    @Test
    void shouldRetryOnServerErrorThenSucceed() {
        wireMock.stubFor(post(urlEqualTo("/api/v1/quotes"))
                .inScenario("retry")
                .whenScenarioStateIs("Started")
                .willReturn(aResponse().withStatus(500).withBody("boom"))
                .willSetStateTo("recovered"));
        wireMock.stubFor(post(urlEqualTo("/api/v1/quotes"))
                .inScenario("retry")
                .whenScenarioStateIs("recovered")
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody(quotesJson("STD", "2026-11-01", "400.00"))));

        Optional<PricingQuotesResponse> response = pricingClient.fetchQuotes(sampleRequest());

        assertThat(response).isPresent();
        wireMock.verify(2, postRequestedFor(urlEqualTo("/api/v1/quotes")));
    }

    @Test
    void shouldOpenCircuitBreakerAfterRepeatedFailures() {
        wireMock.stubFor(post(urlEqualTo("/api/v1/quotes"))
                .willReturn(aResponse().withStatus(500).withBody("down")));

        for (int i = 0; i < 6; i++) {
            assertThat(pricingClient.fetchQuotes(sampleRequest())).isEmpty();
        }

        await().atMost(2, TimeUnit.SECONDS).untilAsserted(() -> assertThat(
                        circuitBreakerRegistry.circuitBreaker("pricing").getState())
                .isEqualTo(CircuitBreaker.State.OPEN));

        int before = wireMock.getAllServeEvents().size();
        assertThat(pricingClient.fetchQuotes(sampleRequest())).isEmpty();
        assertThat(wireMock.getAllServeEvents().size()).isLessThanOrEqualTo(before + 1);
    }

    @Test
    void shouldFallbackOnReadTimeout() {
        wireMock.stubFor(post(urlEqualTo("/api/v1/quotes"))
                .willReturn(aResponse()
                        .withFixedDelay(2500)
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody(quotesJson("STD", "2026-11-01", "400.00"))));

        Optional<PricingQuotesResponse> response = pricingClient.fetchQuotes(sampleRequest());

        assertThat(response).isEmpty();
    }

    @Test
    void shouldFallbackOnMalformedJson() {
        wireMock.stubFor(post(urlEqualTo("/api/v1/quotes"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody("{not-json")));

        Optional<PricingQuotesResponse> response = pricingClient.fetchQuotes(sampleRequest());

        assertThat(response).isEmpty();
    }

    private static PricingQuotesRequest sampleRequest() {
        return new PricingQuotesRequest(
                UUID.randomUUID(),
                List.of(new PricingQuoteItemRequest(
                        "STD",
                        LocalDate.of(2026, 11, 1),
                        new BigDecimal("350.00"),
                        new BigDecimal("200.00"),
                        new BigDecimal("800.00"),
                        0.4,
                        6,
                        10)));
    }

    private static String quotesJson(String code, String date, String price) {
        return """
                {
                  "modelVersion": "fixture-v1",
                  "items": [
                    {
                      "roomTypeCode": "%s",
                      "date": "%s",
                      "price": "%s",
                      "multiplier": 1.25,
                      "demandIndicator": 42,
                      "factors": {"occ": 0.4},
                      "modelVersion": "fixture-v1"
                    }
                  ]
                }
                """
                .formatted(code, date, price);
    }

    /**
     * Narrow slice — deliberately {@code @Configuration} (not {@code @SpringBootConfiguration})
     * so other ITs in this package still discover {@code PmsCoreApplication}.
     */
    @Configuration
    @EnableAutoConfiguration(
            exclude = {DataSourceAutoConfiguration.class, HibernateJpaAutoConfiguration.class})
    @Import({PricingClientConfig.class, PricingClient.class, PricingHttpGateway.class})
    static class TestApplication {}
}
