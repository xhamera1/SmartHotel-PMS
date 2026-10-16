package pl.smarthotel.pms.pricing;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.github.tomakehurst.wiremock.client.WireMock;

import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.PmsCoreApplication;
import pl.smarthotel.pms.database.PostgresFixture;
import pl.smarthotel.pms.ratecalendar.PriceSource;
import pl.smarthotel.pms.ratecalendar.RateCalendarRepository;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

/**
 * Cross-service style IT: pms-core + Postgres + WireMock stand-in for pricing-service.
 * Verifies refresh populates rate_calendar and booking survives pricing outage.
 */
@Testcontainers
@SpringBootTest(classes = PmsCoreApplication.class)
@AutoConfigureMockMvc
@ActiveProfiles("test")
class CrossServiceIT {

    @Container
    static final PostgreSQLContainer POSTGRES = PostgresFixture.postgres();

    @RegisterExtension
    static WireMockExtension pricing =
            WireMockExtension.newInstance().options(wireMockConfig().dynamicPort()).build();

    @DynamicPropertySource
    static void registerProps(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("app.pricing.enabled", () -> "true");
        registry.add("app.pricing.base-url", pricing::baseUrl);
        registry.add("app.pricing.api-key", () -> "cross-service-key");
        registry.add("app.pricing.refresh-horizon-days", () -> "3");
        registry.add("app.pricing.refresh-chunk-size", () -> "50");
        registry.add("app.pricing.connect-timeout-ms", () -> "500");
        registry.add("app.pricing.batch-read-timeout-ms", () -> "2000");
        registry.add("resilience4j.retry.instances.pricing.max-attempts", () -> "1");
    }

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private RateCalendarRepository rateCalendarRepository;

    @Autowired
    private RoomTypeRepository roomTypeRepository;

    @Test
    @WithMockUser(roles = "ADMIN")
    void refreshPopulatesRateCalendarFromPricingQuotes() throws Exception {
        long before = rateCalendarRepository.count();
        pricing.stubFor(WireMock.post(urlEqualTo("/api/v1/quotes"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody(quotesForHorizon())));

        mockMvc.perform(post("/api/v1/admin/pricing/refresh"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("OK"))
                .andExpect(jsonPath("$.daysUpdated").value(org.hamcrest.Matchers.greaterThan(0)));

        assertThat(rateCalendarRepository.count()).isGreaterThan(before);
        assertThat(rateCalendarRepository.findAll())
                .anyMatch(e -> e.getSource() == PriceSource.ML_MODEL && e.getModelVersion() != null);
    }

    @Test
    void bookingSucceedsWhenPricingIsDown() throws Exception {
        pricing.stubFor(WireMock.post(urlEqualTo("/api/v1/quotes"))
                .willReturn(aResponse().withStatus(503).withBody("down")));

        String body =
                """
                {
                  "roomTypeCode": "STD",
                  "ratePlanCode": "FLEX",
                  "checkIn": "%s",
                  "checkOut": "%s",
                  "adults": 2,
                  "guest": {
                    "email": "cross-service-guest@example.com",
                    "firstName": "Cross",
                    "lastName": "Service"
                  }
                }
                """
                        .formatted(LocalDate.now().plusDays(40), LocalDate.now().plusDays(42));

        mockMvc.perform(post("/api/v1/reservations")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isCreated());
    }

    private String quotesForHorizon() {
        LocalDate start = LocalDate.now(java.time.ZoneId.of("Europe/Warsaw"));
        StringBuilder items = new StringBuilder();
        List<String> codes = roomTypeRepository.findByActiveTrueOrderByCodeAsc().stream()
                .map(rt -> rt.getCode())
                .toList();
        boolean first = true;
        for (String code : codes) {
            for (int i = 0; i < 3; i++) {
                if (!first) {
                    items.append(',');
                }
                first = false;
                LocalDate d = start.plusDays(i);
                items.append(
                        """
                        {
                          "roomTypeCode": "%s",
                          "date": "%s",
                          "price": "399.00",
                          "multiplier": 1.1,
                          "demandIndicator": 33,
                          "factors": {"test": true},
                          "modelVersion": "cross-v1"
                        }
                        """
                                .formatted(code, d));
            }
        }
        return "{\"modelVersion\":\"cross-v1\",\"items\":[" + items + "]}";
    }
}
