package pl.smarthotel.pms.ratecalendar;

import static org.assertj.core.api.Assertions.assertThat;
import static pl.smarthotel.pms.auth.AuthTestSupport.adminToken;
import static pl.smarthotel.pms.auth.AuthTestSupport.bearer;
import static pl.smarthotel.pms.auth.AuthTestSupport.receptionToken;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.common.web.ProblemTypes;
import pl.smarthotel.pms.database.PostgresFixture;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class RateCalendarApiIT {

    @Container
    static final PostgreSQLContainer POSTGRES = PostgresFixture.postgres();

    @DynamicPropertySource
    static void registerDataSource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }

    @Autowired
    private TestRestTemplate rest;

    private String admin;
    private String reception;

    @BeforeEach
    void tokens() {
        admin = adminToken(rest);
        reception = receptionToken(rest);
    }

    @Test
    void getPutAndDeleteManualOverride() {
        LocalDate from = LocalDate.of(2026, 11, 1);
        LocalDate to = LocalDate.of(2026, 11, 3);

        ResponseEntity<RateCalendarResponse> calendar = rest.exchange(
                "/api/v1/admin/rate-calendar?roomTypeCode=STD&from=" + from + "&to=" + to,
                HttpMethod.GET,
                bearer(reception),
                RateCalendarResponse.class);
        assertThat(calendar.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(calendar.getBody().days()).hasSize(2);
        assertThat(calendar.getBody().days().getFirst().source()).isIn(PriceSource.BASE, PriceSource.ML_MODEL);

        RateCalendarDayResponse overridden = rest.exchange(
                        "/api/v1/admin/rate-calendar/STD/" + from,
                        HttpMethod.PUT,
                        bearer(admin, Map.of("price", new BigDecimal("333.50"))),
                        RateCalendarDayResponse.class)
                .getBody();
        assertThat(overridden.source()).isEqualTo(PriceSource.MANUAL);
        assertThat(overridden.price()).isEqualByComparingTo("333.50");

        ProblemDetail forbidden = rest.exchange(
                        "/api/v1/admin/rate-calendar/STD/" + from,
                        HttpMethod.PUT,
                        bearer(reception, Map.of("price", new BigDecimal("200.00"))),
                        ProblemDetail.class)
                .getBody();
        assertThat(forbidden.getStatus()).isEqualTo(403);

        assertThat(rest.exchange(
                        "/api/v1/admin/rate-calendar/STD/" + from,
                        HttpMethod.DELETE,
                        bearer(admin),
                        Void.class)
                .getStatusCode())
                .isEqualTo(HttpStatus.NO_CONTENT);

        RateCalendarResponse afterDelete = rest.exchange(
                        "/api/v1/admin/rate-calendar?roomTypeCode=STD&from=" + from + "&to=" + from.plusDays(1),
                        HttpMethod.GET,
                        bearer(admin),
                        RateCalendarResponse.class)
                .getBody();
        assertThat(afterDelete.days().getFirst().fromCalendar()).isFalse();
        assertThat(afterDelete.days().getFirst().source()).isEqualTo(PriceSource.BASE);
    }

    @Test
    void rejectOverrideOutsideMinMax() {
        ProblemDetail bad = rest.exchange(
                        "/api/v1/admin/rate-calendar/STD/2026-12-01",
                        HttpMethod.PUT,
                        bearer(admin, Map.of("price", new BigDecimal("1.00"))),
                        ProblemDetail.class)
                .getBody();
        assertThat(bad.getType().toString()).isEqualTo(ProblemTypes.VALIDATION_ERROR);
    }
}
