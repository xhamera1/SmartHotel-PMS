package pl.smarthotel.pms.guests;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.common.web.PageResponse;
import pl.smarthotel.pms.common.web.ProblemTypes;
import pl.smarthotel.pms.database.PostgresFixture;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class GuestsAdminApiIT {

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

    @Autowired
    private GuestService guestService;

    @Autowired
    private GuestRepository guestRepository;

    @Autowired
    private JdbcTemplate jdbc;

    @Test
    void crudSearchAndEmailUniqueness() {
        var created = rest.postForEntity(
                "/api/v1/admin/guests",
                Map.of(
                        "firstName", "Jan",
                        "lastName", "Kowalski",
                        "email", "jan.kowalski@example.com",
                        "phone", "+48 600 100 200"),
                GuestResponse.class);
        assertThat(created.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(created.getBody().email()).isEqualTo("jan.kowalski@example.com");

        var duplicate = rest.postForEntity(
                "/api/v1/admin/guests",
                Map.of(
                        "firstName", "Jan",
                        "lastName", "Other",
                        "email", "JAN.KOWALSKI@example.com"),
                ProblemDetail.class);
        assertThat(duplicate.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(duplicate.getBody().getType().toString()).isEqualTo(ProblemTypes.CONFLICT);

        var search = rest.exchange(
                "/api/v1/admin/guests?query=kowal&page=0&size=10",
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<PageResponse<GuestResponse>>() {});
        assertThat(search.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(search.getBody().content())
                .extracting(GuestResponse::email)
                .contains("jan.kowalski@example.com");

        Long id = created.getBody().id();
        var updated = rest.exchange(
                        "/api/v1/admin/guests/" + id,
                        HttpMethod.PUT,
                        new HttpEntity<>(Map.of(
                                "firstName", "Janusz",
                                "lastName", "Kowalski",
                                "email", "jan.kowalski@example.com",
                                "phone", "+48 600 100 201")),
                        GuestResponse.class)
                .getBody();
        assertThat(updated.firstName()).isEqualTo("Janusz");
        assertThat(updated.phone()).isEqualTo("+48 600 100 201");

        var deleted = rest.exchange(
                "/api/v1/admin/guests/" + id, HttpMethod.DELETE, null, Void.class);
        assertThat(deleted.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
    }

    @Test
    void findOrCreateDeduplicatesByEmailAndRefreshesProfile() {
        GuestEntity first = guestService.findOrCreate(new GuestUpsertRequest(
                "Anna", "Nowak", "anna@example.com", "+48 111"));
        GuestEntity second = guestService.findOrCreate(new GuestUpsertRequest(
                "Anna Maria", "Nowak-Kowalska", "ANNA@example.com", "+48 222"));

        assertThat(second.getId()).isEqualTo(first.getId());
        assertThat(guestRepository.count()).isEqualTo(1);
        assertThat(second.getFirstName()).isEqualTo("Anna Maria");
        assertThat(second.getLastName()).isEqualTo("Nowak-Kowalska");
        assertThat(second.getEmail()).isEqualTo("ANNA@example.com");
        assertThat(second.getPhone()).isEqualTo("+48 222");
    }

    @Test
    void cannotDeleteGuestWithReservations() {
        Long guestId = jdbc.queryForObject(
                """
                INSERT INTO pms.guests (first_name, last_name, email)
                VALUES ('Piotr', 'Wisniewski', 'piotr@example.com')
                RETURNING id
                """,
                Long.class);
        Long roomTypeId = jdbc.queryForObject(
                "SELECT id FROM pms.room_types WHERE code = 'STD' LIMIT 1", Long.class);
        Long roomId = jdbc.queryForObject(
                """
                INSERT INTO pms.rooms (room_number, room_type_id, status)
                VALUES ('G01', ?, 'AVAILABLE')
                RETURNING id
                """,
                Long.class,
                roomTypeId);
        Long ratePlanId = jdbc.queryForObject(
                "SELECT id FROM pms.rate_plans WHERE code = 'FLEX' LIMIT 1", Long.class);
        jdbc.update(
                """
                INSERT INTO pms.reservations (
                  confirmation_code, guest_id, room_id, rate_plan_id,
                  check_in, check_out, status, adults, total_price, price_breakdown, source)
                VALUES ('GUESTDEL1', ?, ?, ?, '2026-12-01', '2026-12-03',
                        'CANCELLED', 1, 100.00, '[]'::jsonb, 'ADMIN')
                """,
                guestId,
                roomId,
                ratePlanId);

        var response = rest.exchange(
                "/api/v1/admin/guests/" + guestId,
                HttpMethod.DELETE,
                null,
                ProblemDetail.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(response.getBody().getDetail()).contains("reservations still reference");
    }
}
