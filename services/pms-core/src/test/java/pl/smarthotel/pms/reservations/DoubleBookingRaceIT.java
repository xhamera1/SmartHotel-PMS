package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
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
import pl.smarthotel.pms.rooms.CreateRoomRequest;
import pl.smarthotel.pms.rooms.CreateRoomTypeRequest;
import pl.smarthotel.pms.rooms.RoomResponse;
import pl.smarthotel.pms.rooms.RoomStatus;
import pl.smarthotel.pms.rooms.RoomTypeResponse;

/**
 * Two parallel bookings for the last room of a type — exactly one wins; the loser gets
 * {@code room-no-longer-available} (empty inventory after commit, or {@code no_double_booking}).
 */
@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class DoubleBookingRaceIT {

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

    @Test
    void exactlyOneOfTwoParallelBookingsSucceeds() throws Exception {
        LocalDate checkIn = LocalDate.now(WARSAW).plusDays(90);
        LocalDate checkOut = checkIn.plusDays(2);

        RoomTypeResponse type = rest.postForEntity(
                        "/api/v1/admin/room-types",
                        new CreateRoomTypeRequest(
                                "RACE",
                                "Race Single",
                                null,
                                (short) 2,
                                new BigDecimal("200.00"),
                                new BigDecimal("150.00"),
                                new BigDecimal("400.00"),
                                List.of(),
                                true),
                        RoomTypeResponse.class)
                .getBody();
        rest.postForEntity(
                "/api/v1/admin/rooms",
                new CreateRoomRequest("R01", type.id(), (short) 1, RoomStatus.AVAILABLE, null),
                RoomResponse.class);

        CountDownLatch ready = new CountDownLatch(2);
        CountDownLatch start = new CountDownLatch(1);
        AtomicInteger successes = new AtomicInteger();
        AtomicInteger conflicts = new AtomicInteger();
        List<HttpStatus> statuses = Collections.synchronizedList(new ArrayList<>());

        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            List<Future<?>> futures = List.of(
                    pool.submit(() -> {
                        try {
                            book(ready, start, successes, conflicts, statuses, checkIn, checkOut, "a");
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            throw new RuntimeException(e);
                        }
                    }),
                    pool.submit(() -> {
                        try {
                            book(ready, start, successes, conflicts, statuses, checkIn, checkOut, "b");
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            throw new RuntimeException(e);
                        }
                    }));

            assertThat(ready.await(30, TimeUnit.SECONDS)).isTrue();
            start.countDown();
            for (Future<?> future : futures) {
                future.get(60, TimeUnit.SECONDS);
            }
        } finally {
            pool.shutdownNow();
        }

        assertThat(successes.get()).as("exactly one booking must succeed").isEqualTo(1);
        assertThat(conflicts.get()).as("the other booking must conflict").isEqualTo(1);
        assertThat(statuses).containsExactlyInAnyOrder(HttpStatus.CREATED, HttpStatus.CONFLICT);

        Long reserved = jdbc.queryForObject(
                """
                SELECT COUNT(*) FROM pms.reservations res
                JOIN pms.rooms r ON r.id = res.room_id
                WHERE r.room_type_id = ?
                  AND res.check_in = ?
                  AND res.check_out = ?
                  AND res.status IN ('CONFIRMED', 'CHECKED_IN')
                """,
                Long.class,
                type.id(),
                checkIn,
                checkOut);
        assertThat(reserved).isEqualTo(1L);
    }

    private void book(
            CountDownLatch ready,
            CountDownLatch start,
            AtomicInteger successes,
            AtomicInteger conflicts,
            List<HttpStatus> statuses,
            LocalDate checkIn,
            LocalDate checkOut,
            String suffix)
            throws InterruptedException {
        ready.countDown();
        assertThat(start.await(30, TimeUnit.SECONDS)).isTrue();

        ResponseEntity<String> response = rest.postForEntity(
                "/api/v1/reservations",
                Map.of(
                        "roomTypeCode",
                        "RACE",
                        "ratePlanCode",
                        "FLEX",
                        "checkIn",
                        checkIn.toString(),
                        "checkOut",
                        checkOut.toString(),
                        "adults",
                        2,
                        "guest",
                        Map.of(
                                "firstName",
                                "Race",
                                "lastName",
                                suffix,
                                "email",
                                "race." + suffix + "@example.com")),
                String.class);

        statuses.add(HttpStatus.valueOf(response.getStatusCode().value()));
        if (response.getStatusCode() == HttpStatus.CREATED) {
            successes.incrementAndGet();
        } else if (response.getStatusCode() == HttpStatus.CONFLICT) {
            conflicts.incrementAndGet();
            assertThat(response.getBody()).contains(ProblemTypes.ROOM_NO_LONGER_AVAILABLE);
        } else {
            throw new AssertionError(
                    "Unexpected status: " + response.getStatusCode() + " body=" + response.getBody());
        }
    }
}
