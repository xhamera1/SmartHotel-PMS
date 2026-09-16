package pl.smarthotel.pms.rooms;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.util.List;
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
class RoomsAdminApiIT {

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
    private JdbcTemplate jdbc;

    @Test
    void roomTypeCrudValidatesPriceBandAndBlocksDeleteWhenRoomsExist() {
        var invalid = rest.postForEntity(
                "/api/v1/admin/room-types",
                Map.of(
                        "code", "BAD",
                        "name", "Bad band",
                        "capacity", 2,
                        "basePrice", 100,
                        "minPrice", 200,
                        "maxPrice", 300,
                        "amenities", List.of()),
                ProblemDetail.class);
        assertThat(invalid.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(invalid.getBody().getType().toString()).isEqualTo(ProblemTypes.VALIDATION_ERROR);

        var created = rest.postForEntity(
                "/api/v1/admin/room-types",
                Map.of(
                        "code", "ECO",
                        "name", "Economy",
                        "capacity", 2,
                        "basePrice", 250,
                        "minPrice", 180,
                        "maxPrice", 400,
                        "amenities", List.of("wifi"),
                        "active", true),
                RoomTypeResponse.class);
        assertThat(created.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(created.getBody().code()).isEqualTo("ECO");
        assertThat(created.getBody().currency()).isEqualTo("PLN");
        Long roomTypeId = created.getBody().id();

        var listed = rest.exchange(
                "/api/v1/admin/room-types?query=eco&active=true&page=0&size=10",
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<PageResponse<RoomTypeResponse>>() {});
        assertThat(listed.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(listed.getBody().content()).extracting(RoomTypeResponse::code).contains("ECO");

        var room = rest.postForEntity(
                "/api/v1/admin/rooms",
                Map.of(
                        "roomNumber", "901",
                        "roomTypeId", roomTypeId,
                        "floor", 9,
                        "status", "AVAILABLE"),
                RoomResponse.class);
        assertThat(room.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(room.getBody().roomTypeCode()).isEqualTo("ECO");

        var deleteBlocked = rest.exchange(
                "/api/v1/admin/room-types/" + roomTypeId,
                HttpMethod.DELETE,
                null,
                ProblemDetail.class);
        assertThat(deleteBlocked.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(deleteBlocked.getBody().getDetail()).contains("rooms are still assigned");

        // Remove the room via JDBC so delete of an unused type can succeed.
        jdbc.update("DELETE FROM pms.rooms WHERE id = ?", room.getBody().id());

        var deleted = rest.exchange(
                "/api/v1/admin/room-types/" + roomTypeId, HttpMethod.DELETE, null, Void.class);
        assertThat(deleted.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
    }

    @Test
    void cannotDeleteRoomTypeWithActiveReservation() {
        var roomType = rest.postForEntity(
                        "/api/v1/admin/room-types",
                        Map.of(
                                "code", "ACT",
                                "name", "Active Test",
                                "capacity", 2,
                                "basePrice", 300,
                                "minPrice", 200,
                                "maxPrice", 500,
                                "amenities", List.of()),
                        RoomTypeResponse.class)
                .getBody();
        var room = rest.postForEntity(
                        "/api/v1/admin/rooms",
                        Map.of(
                                "roomNumber", "902",
                                "roomTypeId", roomType.id(),
                                "status", "AVAILABLE"),
                        RoomResponse.class)
                .getBody();

        Long guestId = jdbc.queryForObject(
                """
                INSERT INTO pms.guests (first_name, last_name, email)
                VALUES ('Anna', 'Nowak', 'anna.nowak@example.com')
                RETURNING id
                """,
                Long.class);
        Long ratePlanId = jdbc.queryForObject(
                "SELECT id FROM pms.rate_plans WHERE code = 'FLEX' LIMIT 1", Long.class);

        jdbc.update(
                """
                INSERT INTO pms.reservations (
                  confirmation_code, guest_id, room_id, rate_plan_id,
                  check_in, check_out, status, adults, total_price, price_breakdown, source)
                VALUES ('ACTVTEST1', ?, ?, ?, '2026-11-01', '2026-11-03',
                        'CONFIRMED', 2, 600.00, '[]'::jsonb, 'ADMIN')
                """,
                guestId,
                room.id(),
                ratePlanId);

        var response = rest.exchange(
                "/api/v1/admin/room-types/" + roomType.id(),
                HttpMethod.DELETE,
                HttpEntity.EMPTY,
                ProblemDetail.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        assertThat(response.getBody().getDetail()).contains("active reservations");
    }

    @Test
    void roomUpdateAndFilterByStatus() {
        Long roomTypeId = rest.postForEntity(
                        "/api/v1/admin/room-types",
                        Map.of(
                                "code", "FLT",
                                "name", "Filter Type",
                                "capacity", 2,
                                "basePrice", 220.50,
                                "minPrice", 150,
                                "maxPrice", 350,
                                "amenities", List.of()),
                        RoomTypeResponse.class)
                .getBody()
                .id();

        Long roomId = rest.postForEntity(
                        "/api/v1/admin/rooms",
                        Map.of(
                                "roomNumber", "903",
                                "roomTypeId", roomTypeId,
                                "status", "AVAILABLE"),
                        RoomResponse.class)
                .getBody()
                .id();

        var updated = rest.exchange(
                        "/api/v1/admin/rooms/" + roomId,
                        HttpMethod.PUT,
                        new HttpEntity<>(Map.of(
                                "roomNumber", "903",
                                "roomTypeId", roomTypeId,
                                "floor", 3,
                                "status", "OUT_OF_SERVICE",
                                "notes", "maintenance")),
                        RoomResponse.class)
                .getBody();
        assertThat(updated.status()).isEqualTo(RoomStatus.OUT_OF_SERVICE);
        assertThat(updated.notes()).isEqualTo("maintenance");

        var filtered = rest.exchange(
                "/api/v1/admin/rooms?status=OUT_OF_SERVICE&roomTypeId=" + roomTypeId,
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<PageResponse<RoomResponse>>() {});
        assertThat(filtered.getBody().content())
                .extracting(RoomResponse::roomNumber)
                .contains("903");
        assertThat(new BigDecimal("220.50")).isEqualByComparingTo("220.50");
    }
}
