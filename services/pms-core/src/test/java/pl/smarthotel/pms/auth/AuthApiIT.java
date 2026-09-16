package pl.smarthotel.pms.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static pl.smarthotel.pms.auth.AuthTestSupport.ADMIN_EMAIL;
import static pl.smarthotel.pms.auth.AuthTestSupport.ADMIN_PASSWORD;
import static pl.smarthotel.pms.auth.AuthTestSupport.RECEPTION_EMAIL;
import static pl.smarthotel.pms.auth.AuthTestSupport.RECEPTION_PASSWORD;
import static pl.smarthotel.pms.auth.AuthTestSupport.adminToken;
import static pl.smarthotel.pms.auth.AuthTestSupport.bearer;
import static pl.smarthotel.pms.auth.AuthTestSupport.cookieHeader;
import static pl.smarthotel.pms.auth.AuthTestSupport.extractRefreshCookie;
import static pl.smarthotel.pms.auth.AuthTestSupport.receptionToken;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
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
import pl.smarthotel.pms.rooms.RoomTypeResponse;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class AuthApiIT {

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
    void loginRefreshAndRoleGuards() {
        ResponseEntity<TokenResponse> login = rest.postForEntity(
                "/api/v1/auth/login",
                Map.of("email", ADMIN_EMAIL, "password", ADMIN_PASSWORD),
                TokenResponse.class);
        assertThat(login.getStatusCode()).isEqualTo(HttpStatus.OK);
        TokenResponse tokens = login.getBody();
        assertThat(tokens).isNotNull();
        assertThat(tokens.role()).isEqualTo(StaffRole.ADMIN);
        assertThat(tokens.tokenType()).isEqualTo("Bearer");
        assertThat(tokens.expiresIn()).isEqualTo(3600);
        assertThat(tokens.accessToken()).isNotBlank();

        String refreshCookie = extractRefreshCookie(login);
        assertThat(refreshCookie).isNotBlank();

        ResponseEntity<TokenResponse> refreshed = rest.exchange(
                "/api/v1/auth/refresh",
                HttpMethod.POST,
                new HttpEntity<>(cookieHeader(refreshCookie)),
                TokenResponse.class);
        assertThat(refreshed.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refreshed.getBody()).isNotNull();
        assertThat(refreshed.getBody().accessToken()).isNotBlank();
        assertThat(extractRefreshCookie(refreshed)).isNotBlank();

        ProblemDetail badLogin = rest.postForEntity(
                        "/api/v1/auth/login",
                        Map.of("email", ADMIN_EMAIL, "password", "wrong-password"),
                        ProblemDetail.class)
                .getBody();
        assertThat(badLogin.getStatus()).isEqualTo(401);
        assertThat(badLogin.getType().toString()).isEqualTo(ProblemTypes.UNAUTHORIZED);

        assertThat(rest.getForEntity(
                        "/api/v1/availability?checkIn=2026-10-03&checkOut=2026-10-05&guests=2",
                        String.class)
                .getStatusCode())
                .isEqualTo(HttpStatus.OK);

        assertThat(rest.getForEntity("/api/v1/admin/room-types", ProblemDetail.class).getStatusCode())
                .isEqualTo(HttpStatus.UNAUTHORIZED);

        String admin = adminToken(rest);
        assertThat(rest.exchange(
                        "/api/v1/admin/room-types?page=0&size=5",
                        HttpMethod.GET,
                        bearer(admin),
                        String.class)
                .getStatusCode())
                .isEqualTo(HttpStatus.OK);

        String reception = receptionToken(rest);
        ProblemDetail forbidden = rest.exchange(
                        "/api/v1/admin/room-types",
                        HttpMethod.POST,
                        bearer(
                                reception,
                                Map.of(
                                        "code",
                                        "X1",
                                        "name",
                                        "Nope",
                                        "capacity",
                                        2,
                                        "basePrice",
                                        200,
                                        "minPrice",
                                        100,
                                        "maxPrice",
                                        300,
                                        "amenities",
                                        List.of())),
                        ProblemDetail.class)
                .getBody();
        assertThat(forbidden.getStatus()).isEqualTo(403);
        assertThat(forbidden.getType().toString()).isEqualTo(ProblemTypes.FORBIDDEN);

        assertThat(rest.exchange(
                        "/api/v1/admin/guests?page=0&size=5",
                        HttpMethod.GET,
                        bearer(reception),
                        String.class)
                .getStatusCode())
                .isEqualTo(HttpStatus.OK);

        ProblemDetail refreshAsAccess = rest.exchange(
                        "/api/v1/admin/room-types",
                        HttpMethod.GET,
                        bearer(refreshCookie),
                        ProblemDetail.class)
                .getBody();
        assertThat(refreshAsAccess.getStatus()).isEqualTo(401);

        ResponseEntity<RoomTypeResponse> created = rest.exchange(
                "/api/v1/admin/room-types",
                HttpMethod.POST,
                bearer(
                        admin,
                        Map.of(
                                "code",
                                "AUTH",
                                "name",
                                "Auth Type",
                                "capacity",
                                2,
                                "basePrice",
                                200,
                                "minPrice",
                                100,
                                "maxPrice",
                                300,
                                "amenities",
                                List.of())),
                RoomTypeResponse.class);
        assertThat(created.getStatusCode()).isEqualTo(HttpStatus.CREATED);

        ResponseEntity<Void> logout = rest.exchange(
                "/api/v1/auth/logout",
                HttpMethod.POST,
                new HttpEntity<>(cookieHeader(refreshCookie)),
                Void.class);
        assertThat(logout.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        assertThat(extractRefreshCookie(logout)).isIn("", null);

        assertThat(RECEPTION_EMAIL).contains("reception");
    }
}
