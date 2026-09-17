package pl.smarthotel.pms.common.security;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithAnonymousUser;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultMatcher;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.database.PostgresFixture;

/**
 * Table-driven security matrix (Phase 2 QA): anonymous / RECEPTIONIST / ADMIN × endpoint.
 * Filter chain still applies; {@code @WithMockUser} supplies the authenticated principal.
 */
@Testcontainers
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class SecurityMatrixIT {

    @Container
    static final PostgreSQLContainer POSTGRES = PostgresFixture.postgres();

    @DynamicPropertySource
    static void registerDataSource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }

    @Autowired
    private MockMvc mockMvc;

    @ParameterizedTest(name = "anonymous {0} → {1}")
    @CsvSource({
        "GET,/api/v1/availability?checkIn=2026-10-03&checkOut=2026-10-05&guests=2,200",
        "GET,/api/v1/admin/guests,401",
        "GET,/api/v1/admin/room-types,401",
        "GET,/api/v1/admin/rate-calendar?roomTypeCode=STD&from=2026-10-01&to=2026-10-03,401",
        "GET,/api/v1/admin/dashboard/kpis,401"
    })
    @WithAnonymousUser
    void anonymousMatrix(String method, String path, int status) throws Exception {
        perform(method, path, statusMatcher(status));
    }

    @ParameterizedTest(name = "receptionist {0} → {1}")
    @CsvSource({
        "GET,/api/v1/admin/guests?page=0&size=5,200",
        "GET,/api/v1/admin/reservations?page=0&size=5,200",
        "GET,/api/v1/admin/dashboard/kpis,200",
        "GET,/api/v1/admin/rate-calendar?roomTypeCode=STD&from=2026-10-01&to=2026-10-03,200",
        "GET,/api/v1/admin/room-types?page=0&size=5,200",
        "PUT,/api/v1/admin/rate-calendar/STD/2026-10-01,403"
    })
    @WithMockUser(roles = "RECEPTIONIST")
    void receptionistMatrix(String method, String path, int status) throws Exception {
        perform(method, path, statusMatcher(status));
    }

    @ParameterizedTest(name = "admin {0} → {1}")
    @CsvSource({
        "GET,/api/v1/admin/room-types?page=0&size=5,200",
        "GET,/api/v1/admin/rooms?page=0&size=5,200",
        "GET,/api/v1/admin/guests?page=0&size=5,200",
        "GET,/api/v1/admin/dashboard/kpis,200",
        "GET,/api/v1/admin/rate-plans,200"
    })
    @WithMockUser(roles = "ADMIN")
    void adminMatrix(String method, String path, int status) throws Exception {
        perform(method, path, statusMatcher(status));
    }

    private void perform(String method, String path, ResultMatcher matcher) throws Exception {
        var builders =
                switch (method) {
                    case "GET" -> get(path);
                    case "POST" -> post(path)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("{}");
                    case "PUT" -> put(path)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("{\"price\":200.00}");
                    default -> throw new IllegalArgumentException(method);
                };
        mockMvc.perform(builders).andExpect(matcher);
    }

    private static ResultMatcher statusMatcher(int status) {
        return status().is(status);
    }
}
