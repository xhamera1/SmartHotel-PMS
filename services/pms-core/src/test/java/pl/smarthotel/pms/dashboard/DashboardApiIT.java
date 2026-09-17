package pl.smarthotel.pms.dashboard;

import static org.assertj.core.api.Assertions.assertThat;
import static pl.smarthotel.pms.auth.AuthTestSupport.adminToken;
import static pl.smarthotel.pms.auth.AuthTestSupport.bearer;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.database.PostgresFixture;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class DashboardApiIT {

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

    @Test
    void kpisAreReachableForStaff() {
        String token = adminToken(rest);
        ResponseEntity<DashboardKpisResponse> response = rest.exchange(
                "/api/v1/admin/dashboard/kpis",
                HttpMethod.GET,
                bearer(token),
                DashboardKpisResponse.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        DashboardKpisResponse body = response.getBody();
        assertThat(body.businessDate()).isNotNull();
        assertThat(body.roomsSellable()).isPositive();
        assertThat(body.currency()).isEqualTo("PLN");
        assertThat(body.occupancyToday()).isNotNull();
        assertThat(body.mtdRevenue()).isNotNull();

        ResponseEntity<DashboardTimeseriesResponse> series = rest.exchange(
                "/api/v1/admin/dashboard/timeseries?days=30",
                HttpMethod.GET,
                bearer(token),
                DashboardTimeseriesResponse.class);
        assertThat(series.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(series.getBody()).isNotNull();
        assertThat(series.getBody().points()).hasSize(30);
        assertThat(series.getBody().currency()).isEqualTo("PLN");
    }
}
