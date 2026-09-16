package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.ProblemDetail;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.common.web.ProblemTypes;
import pl.smarthotel.pms.database.PostgresFixture;
import pl.smarthotel.pms.ratecalendar.PriceSource;
import pl.smarthotel.pms.rooms.CreateRoomRequest;
import pl.smarthotel.pms.rooms.CreateRoomTypeRequest;
import pl.smarthotel.pms.rooms.RoomResponse;
import pl.smarthotel.pms.rooms.RoomStatus;
import pl.smarthotel.pms.rooms.RoomTypeResponse;
import pl.smarthotel.pms.rooms.UpdateRoomRequest;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class AvailabilityApiIT {

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
    void shouldRejectInvalidStayWindow() {
        ProblemDetail problem = rest.getForObject(
                "/api/v1/availability?checkIn=2026-10-05&checkOut=2026-10-05&guests=2",
                ProblemDetail.class);
        assertThat(problem.getStatus()).isEqualTo(400);
        assertThat(problem.getType().toString()).isEqualTo(ProblemTypes.VALIDATION_ERROR);
    }

    @Test
    void shouldFilterByCapacityExcludeOosAllowBackToBackAndUseCalendarOrBase() {
        RoomTypeResponse type = rest.postForEntity(
                        "/api/v1/admin/room-types",
                        new CreateRoomTypeRequest(
                                "AVT",
                                "Avail Test",
                                "TDD fixture",
                                (short) 2,
                                new BigDecimal("200.00"),
                                new BigDecimal("150.00"),
                                new BigDecimal("400.00"),
                                java.util.List.of("wifi"),
                                true),
                        RoomTypeResponse.class)
                .getBody();

        RoomResponse free = createRoom(type.id(), "A01", RoomStatus.AVAILABLE);
        RoomResponse booked = createRoom(type.id(), "A02", RoomStatus.AVAILABLE);
        RoomResponse oos = createRoom(type.id(), "A03", RoomStatus.AVAILABLE);
        rest.put(
                "/api/v1/admin/rooms/" + oos.id(),
                new UpdateRoomRequest("A03", type.id(), (short) 1, RoomStatus.OUT_OF_SERVICE, "paint"),
                RoomResponse.class);

        // Party of 3 cannot use capacity-2 type
        AvailabilityResponse tooBig = rest.getForObject(
                "/api/v1/availability?checkIn=2026-12-01&checkOut=2026-12-03&guests=3",
                AvailabilityResponse.class);
        assertThat(tooBig.roomTypes()).extracting(AvailableRoomTypeAvailability::code).doesNotContain("AVT");

        Long guestId = jdbc.queryForObject(
                """
                INSERT INTO pms.guests (first_name, last_name, email)
                VALUES ('Avail', 'Guest', 'avail.guest@example.com') RETURNING id
                """,
                Long.class);
        Long ratePlanId =
                jdbc.queryForObject("SELECT id FROM pms.rate_plans WHERE code = 'FLEX'", Long.class);

        // Active booking on A02 for [12-01, 12-03)
        jdbc.update(
                """
                INSERT INTO pms.reservations (
                  confirmation_code, guest_id, room_id, rate_plan_id,
                  check_in, check_out, status, adults, total_price, price_breakdown, source)
                VALUES ('AVTEST01', ?, ?, ?, '2026-12-01', '2026-12-03',
                        'CONFIRMED', 2, 400.00, '[]'::jsonb, 'ADMIN')
                """,
                guestId,
                booked.id(),
                ratePlanId);

        // Calendar only for first night — second night must fall back to base
        jdbc.update(
                """
                INSERT INTO pms.rate_calendar (room_type_id, date, price, source)
                VALUES (?, '2026-12-01', 275.00, 'ML_MODEL')
                """,
                type.id());

        AvailabilityResponse response = rest.getForObject(
                "/api/v1/availability?checkIn=2026-12-01&checkOut=2026-12-03&guests=2",
                AvailabilityResponse.class);

        AvailableRoomTypeAvailability avt = response.roomTypes().stream()
                .filter(rt -> "AVT".equals(rt.code()))
                .findFirst()
                .orElseThrow();
        assertThat(avt.roomsLeft()).isEqualTo(1); // A01 only; A02 booked, A03 OOS
        assertThat(avt.nights()).hasSize(2);
        assertThat(avt.nights().get(0).bar()).isEqualByComparingTo("275.00");
        assertThat(avt.nights().get(0).priceSource()).isEqualTo(PriceSource.ML_MODEL);
        assertThat(avt.nights().get(1).bar()).isEqualByComparingTo("200.00");
        assertThat(avt.nights().get(1).priceSource()).isEqualTo(PriceSource.BASE);
        assertThat(avt.ratePlans()).extracting(RatePlanQuote::code).contains("FLEX", "NONREF", "BB");
        // FLEX total = 275 + 200 = 475
        RatePlanQuote flex = avt.ratePlans().stream()
                .filter(p -> "FLEX".equals(p.code()))
                .findFirst()
                .orElseThrow();
        assertThat(flex.totalPrice()).isEqualByComparingTo("475.00");

        // Same-day turnover: check-in on previous check-out must free A02 again
        AvailabilityResponse backToBack = rest.getForObject(
                "/api/v1/availability?checkIn=2026-12-03&checkOut=2026-12-05&guests=2",
                AvailabilityResponse.class);
        AvailableRoomTypeAvailability after = backToBack.roomTypes().stream()
                .filter(rt -> "AVT".equals(rt.code()))
                .findFirst()
                .orElseThrow();
        assertThat(after.roomsLeft()).isEqualTo(2); // A01 + A02

        // Cancelled stay must not block
        jdbc.update(
                """
                INSERT INTO pms.reservations (
                  confirmation_code, guest_id, room_id, rate_plan_id,
                  check_in, check_out, status, adults, total_price, price_breakdown, source)
                VALUES ('AVTEST02', ?, ?, ?, '2026-12-10', '2026-12-12',
                        'CANCELLED', 2, 400.00, '[]'::jsonb, 'ADMIN')
                """,
                guestId,
                free.id(),
                ratePlanId);
        AvailabilityResponse cancelledOk = rest.getForObject(
                "/api/v1/availability?checkIn=2026-12-10&checkOut=2026-12-12&guests=2",
                AvailabilityResponse.class);
        assertThat(cancelledOk.roomTypes().stream()
                        .filter(rt -> "AVT".equals(rt.code()))
                        .findFirst()
                        .orElseThrow()
                        .roomsLeft())
                .isEqualTo(2);

        assertThat(free.roomNumber()).isEqualTo("A01");
        assertThat(Map.of("currency", response.currency())).containsEntry("currency", "PLN");
    }

    private RoomResponse createRoom(Long roomTypeId, String number, RoomStatus status) {
        return rest.postForEntity(
                        "/api/v1/admin/rooms",
                        new CreateRoomRequest(number, roomTypeId, (short) 1, status, null),
                        RoomResponse.class)
                .getBody();
    }
}
