package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;
import static pl.smarthotel.pms.auth.AuthTestSupport.adminToken;
import static pl.smarthotel.pms.auth.AuthTestSupport.bearer;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
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

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ReservationApiIT {

    private static final ZoneId WARSAW = ZoneId.of("Europe/Warsaw");

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

    @Autowired
    private ReservationService reservationService;

    private String token;

    @BeforeEach
    void authenticate() {
        token = adminToken(rest);
    }

    @Test
    void guestCheckoutLookupCancelAndStaffTransitions() {
        LocalDate today = LocalDate.now(WARSAW);
        LocalDate flexIn = today.plusDays(40);
        LocalDate flexOut = flexIn.plusDays(2);
        LocalDate nonrefIn = today.plusDays(50);
        LocalDate nonrefOut = nonrefIn.plusDays(1);

        seedCalendar("STD", flexIn.toString(), "260.00");
        seedCalendar("STD", flexIn.plusDays(1).toString(), "270.00");

        ResponseEntity<ReservationResponse> created = rest.postForEntity(
                "/api/v1/reservations",
                Map.of(
                        "roomTypeCode",
                        "STD",
                        "ratePlanCode",
                        "FLEX",
                        "checkIn",
                        flexIn.toString(),
                        "checkOut",
                        flexOut.toString(),
                        "adults",
                        2,
                        "guest",
                        Map.of(
                                "firstName",
                                "Jan",
                                "lastName",
                                "Kowalski",
                                "email",
                                "jan.lifecycle@example.com",
                                "phone",
                                "+48 600 100 200")),
                ReservationResponse.class);

        assertThat(created.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        ReservationResponse body = created.getBody();
        assertThat(body.confirmationCode()).matches("[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{8}");
        assertThat(body.status()).isEqualTo(ReservationStatus.CONFIRMED);
        assertThat(body.roomType()).isEqualTo("STD");
        assertThat(body.source()).isEqualTo(ReservationSource.WEB);
        assertThat(body.priceBreakdown()).hasSize(2);
        assertThat(body.priceBreakdown().getFirst().priceSource()).isEqualTo(PriceSource.ML_MODEL);
        assertThat(body.totalPrice()).isEqualByComparingTo("530.00");
        assertThat(created.getHeaders().getLocation()).isNotNull();

        ReservationResponse lookedUp = rest.getForObject(
                "/api/v1/reservations/lookup?code={code}&email={email}",
                ReservationResponse.class,
                body.confirmationCode(),
                "jan.lifecycle@example.com");
        assertThat(lookedUp.confirmationCode()).isEqualTo(body.confirmationCode());
        assertThat(lookedUp.roomNumber()).isNotBlank();

        ReservationResponse nonref = rest.postForEntity(
                        "/api/v1/reservations",
                        Map.of(
                                "roomTypeCode",
                                "STD",
                                "ratePlanCode",
                                "NONREF",
                                "checkIn",
                                nonrefIn.toString(),
                                "checkOut",
                                nonrefOut.toString(),
                                "adults",
                                1,
                                "guest",
                                Map.of(
                                        "firstName",
                                        "Ewa",
                                        "lastName",
                                        "Nowak",
                                        "email",
                                        "ewa.nonref@example.com")),
                        ReservationResponse.class)
                .getBody();
        ProblemDetail nonRefundable = rest.postForObject(
                "/api/v1/reservations/" + nonref.confirmationCode() + "/cancel?email=ewa.nonref@example.com",
                null,
                ProblemDetail.class);
        assertThat(nonRefundable.getType().toString()).isEqualTo(ProblemTypes.RATE_PLAN_NOT_REFUNDABLE);

        ReservationResponse cancelled = rest.postForObject(
                "/api/v1/reservations/" + body.confirmationCode() + "/cancel?email=jan.lifecycle@example.com",
                null,
                ReservationResponse.class);
        assertThat(cancelled.status()).isEqualTo(ReservationStatus.CANCELLED);

        ReservationResponse walkIn = rest.exchange(
                        "/api/v1/admin/reservations",
                        HttpMethod.POST,
                        bearer(
                                token,
                                Map.of(
                                        "roomTypeCode",
                                        "DLX",
                                        "ratePlanCode",
                                        "BB",
                                        "checkIn",
                                        today.toString(),
                                        "checkOut",
                                        today.plusDays(2).toString(),
                                        "adults",
                                        2,
                                        "guest",
                                        Map.of(
                                                "firstName",
                                                "Adam",
                                                "lastName",
                                                "Staff",
                                                "email",
                                                "adam.staff@example.com"))),
                        ReservationResponse.class)
                .getBody();
        assertThat(walkIn.source()).isEqualTo(ReservationSource.ADMIN);

        ReservationResponse checkedIn = rest.exchange(
                        "/api/v1/admin/reservations/" + walkIn.id() + "/check-in",
                        HttpMethod.POST,
                        bearer(token),
                        ReservationResponse.class)
                .getBody();
        assertThat(checkedIn.status()).isEqualTo(ReservationStatus.CHECKED_IN);

        ReservationResponse checkedOut = rest.exchange(
                        "/api/v1/admin/reservations/" + walkIn.id() + "/check-out",
                        HttpMethod.POST,
                        bearer(token),
                        ReservationResponse.class)
                .getBody();
        assertThat(checkedOut.status()).isEqualTo(ReservationStatus.CHECKED_OUT);

        ProblemDetail illegal = rest.exchange(
                        "/api/v1/admin/reservations/" + walkIn.id() + "/check-in",
                        HttpMethod.POST,
                        bearer(token),
                        ProblemDetail.class)
                .getBody();
        assertThat(illegal.getType().toString()).isEqualTo(ProblemTypes.ILLEGAL_STATE_TRANSITION);
    }

    @Test
    void adminListAndManualNoShow() {
        LocalDate today = LocalDate.now(WARSAW);
        LocalDate in = today.plusDays(70);
        LocalDate out = in.plusDays(1);

        ReservationResponse booking = rest.postForEntity(
                        "/api/v1/reservations",
                        Map.of(
                                "roomTypeCode",
                                "STD",
                                "ratePlanCode",
                                "FLEX",
                                "checkIn",
                                in.toString(),
                                "checkOut",
                                out.toString(),
                                "adults",
                                2,
                                "guest",
                                Map.of(
                                        "firstName",
                                        "List",
                                        "lastName",
                                        "Guest",
                                        "email",
                                        "list.guest@example.com")),
                        ReservationResponse.class)
                .getBody();

        ResponseEntity<String> listed = rest.exchange(
                "/api/v1/admin/reservations?status=CONFIRMED&query=list.guest&page=0&size=20",
                HttpMethod.GET,
                bearer(token),
                String.class);
        assertThat(listed.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(listed.getBody()).contains(booking.confirmationCode()).contains("list.guest@example.com");

        ReservationResponse noShow = rest.exchange(
                        "/api/v1/admin/reservations/" + booking.id() + "/no-show",
                        HttpMethod.POST,
                        bearer(token),
                        ReservationResponse.class)
                .getBody();
        assertThat(noShow.status()).isEqualTo(ReservationStatus.NO_SHOW);
    }

    @Test
    void nightAuditMarksMissedCheckInsAsNoShow() {
        LocalDate today = LocalDate.now(WARSAW);
        LocalDate missedCheckIn = today.minusDays(3);
        LocalDate missedCheckOut = today.minusDays(1);

        ReservationResponse booking = rest.postForEntity(
                        "/api/v1/reservations",
                        Map.of(
                                "roomTypeCode",
                                "STD",
                                "ratePlanCode",
                                "FLEX",
                                "checkIn",
                                missedCheckIn.toString(),
                                "checkOut",
                                missedCheckOut.toString(),
                                "adults",
                                2,
                                "guest",
                                Map.of(
                                        "firstName",
                                        "No",
                                        "lastName",
                                        "Show",
                                        "email",
                                        "noshow.audit@example.com")),
                        ReservationResponse.class)
                .getBody();
        assertThat(booking.status()).isEqualTo(ReservationStatus.CONFIRMED);

        int marked = reservationService.markNoShows(today);
        assertThat(marked).isGreaterThanOrEqualTo(1);

        ReservationResponse after = rest.getForObject(
                "/api/v1/reservations/lookup?code={code}&email={email}",
                ReservationResponse.class,
                booking.confirmationCode(),
                "noshow.audit@example.com");
        assertThat(after.status()).isEqualTo(ReservationStatus.NO_SHOW);

        assertThat(reservationService.markNoShows(today)).isEqualTo(0);
    }

    @Test
    void createFailsWhenInventoryExhausted() {
        LocalDate in = LocalDate.now(WARSAW).plusDays(60);
        LocalDate out = in.plusDays(2);

        RoomTypeResponse type = rest.exchange(
                        "/api/v1/admin/room-types",
                        HttpMethod.POST,
                        bearer(
                                token,
                                new CreateRoomTypeRequest(
                                        "ONE",
                                        "Single Inventory",
                                        null,
                                        (short) 2,
                                        new BigDecimal("200.00"),
                                        new BigDecimal("150.00"),
                                        new BigDecimal("400.00"),
                                        List.of(),
                                        true)),
                        RoomTypeResponse.class)
                .getBody();
        rest.exchange(
                "/api/v1/admin/rooms",
                HttpMethod.POST,
                bearer(token, new CreateRoomRequest("Z01", type.id(), (short) 1, RoomStatus.AVAILABLE, null)),
                RoomResponse.class);

        rest.postForEntity(
                "/api/v1/reservations",
                Map.of(
                        "roomTypeCode",
                        "ONE",
                        "ratePlanCode",
                        "FLEX",
                        "checkIn",
                        in.toString(),
                        "checkOut",
                        out.toString(),
                        "adults",
                        2,
                        "guest",
                        Map.of(
                                "firstName",
                                "First",
                                "lastName",
                                "Guest",
                                "email",
                                "first.one@example.com")),
                ReservationResponse.class);

        ProblemDetail conflict = rest.postForEntity(
                        "/api/v1/reservations",
                        Map.of(
                                "roomTypeCode",
                                "ONE",
                                "ratePlanCode",
                                "FLEX",
                                "checkIn",
                                in.toString(),
                                "checkOut",
                                out.toString(),
                                "adults",
                                2,
                                "guest",
                                Map.of(
                                        "firstName",
                                        "Second",
                                        "lastName",
                                        "Guest",
                                        "email",
                                        "second.one@example.com")),
                        ProblemDetail.class)
                .getBody();
        assertThat(conflict.getType().toString()).isEqualTo(ProblemTypes.ROOM_NO_LONGER_AVAILABLE);
    }

    private void seedCalendar(String roomTypeCode, String date, String price) {
        jdbc.update(
                """
                INSERT INTO pms.rate_calendar (room_type_id, date, price, source)
                SELECT id, CAST(? AS date), CAST(? AS numeric), 'ML_MODEL'
                FROM pms.room_types WHERE code = ?
                ON CONFLICT (room_type_id, date) DO UPDATE SET price = EXCLUDED.price, source = EXCLUDED.source
                """,
                date,
                price,
                roomTypeCode);
    }
}
