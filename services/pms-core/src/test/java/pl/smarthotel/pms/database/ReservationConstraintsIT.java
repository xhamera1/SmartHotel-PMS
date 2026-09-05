package pl.smarthotel.pms.database;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.stream.Stream;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.ValueSource;
import org.postgresql.util.PSQLException;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

@Testcontainers
class ReservationConstraintsIT {
    private static final LocalDate CHECK_IN = LocalDate.of(2026, 10, 10);
    private static final LocalDate CHECK_OUT = LocalDate.of(2026, 10, 14);

    @Container
    static final PostgreSQLContainer POSTGRES = PostgresFixture.postgres();

    private Connection connection;
    private long guestId;
    private long roomId;
    private long otherRoomId;
    private long ratePlanId;

    @BeforeAll
    static void migrate() {
        PostgresFixture.flyway(POSTGRES, true).migrate();
    }

    @BeforeEach
    void beginTransaction() throws SQLException {
        connection = PostgresFixture.connect(POSTGRES);
        connection.setAutoCommit(false);
        guestId = scalar("""
                INSERT INTO pms.guests (first_name, last_name, email)
                VALUES ('Test', 'Guest', 'constraint-test@example.com') RETURNING id
                """);
        roomId = scalar("SELECT min(id) FROM pms.rooms");
        otherRoomId = scalar("SELECT max(id) FROM pms.rooms");
        ratePlanId = scalar("SELECT id FROM pms.rate_plans WHERE code = 'FLEX'");
    }

    @AfterEach
    void rollbackTransaction() throws SQLException {
        if (connection != null) {
            try {
                connection.rollback();
            } finally {
                connection.close();
            }
        }
    }

    @ParameterizedTest(name = "{0} vs {1}, competing stay {2} to {3}")
    @MethodSource("overlappingStays")
    void shouldRejectOverlappingActiveReservations(
            String existingStatus, String newStatus, LocalDate from, LocalDate to) throws SQLException {
        insert("FIRST", roomId, CHECK_IN, CHECK_OUT, existingStatus);

        var error = assertThrows(PSQLException.class,
                () -> insert("SECOND", roomId, from, to, newStatus));

        assertExclusionViolation(error);
    }

    static Stream<Arguments> overlappingStays() {
        // Identical, partial overlaps on either side, contained, and containing.
        int[][] offsets = {{0, 4}, {-1, 1}, {3, 5}, {1, 3}, {-1, 5}};
        return Stream.of("CONFIRMED", "CHECKED_IN").flatMap(existing ->
                Stream.of("CONFIRMED", "CHECKED_IN").flatMap(incoming ->
                        Stream.of(offsets).map(range -> Arguments.of(existing, incoming,
                                CHECK_IN.plusDays(range[0]), CHECK_IN.plusDays(range[1])))));
    }

    @ParameterizedTest
    @CsvSource({"2026-10-08, 2026-10-10", "2026-10-14, 2026-10-16"})
    void shouldAllowBackToBackStaysOnSameRoom(LocalDate from, LocalDate to) throws SQLException {
        insert("FIRST", roomId, CHECK_IN, CHECK_OUT, "CHECKED_IN");
        insert("SECOND", roomId, from, to, "CONFIRMED");

        assertEquals(2, scalar("SELECT count(*) FROM pms.reservations"));
        assertEquals(1, scalar("""
                SELECT count(*) FROM pms.reservations WHERE confirmation_code = 'FIRST'
                  AND lower(stay) = check_in AND upper(stay) = check_out
                  AND lower_inc(stay) AND NOT upper_inc(stay)
                """));
    }

    @Test
    void shouldAllowSameDatesForDifferentRooms() throws SQLException {
        insert("FIRST", roomId, CHECK_IN, CHECK_OUT, "CONFIRMED");
        insert("SECOND", otherRoomId, CHECK_IN, CHECK_OUT, "CONFIRMED");

        assertEquals(2, scalar("SELECT count(*) FROM pms.reservations"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"CANCELLED", "NO_SHOW", "CHECKED_OUT"})
    void shouldAllowNewBookingAfterRoomIsReleased(String terminalStatus) throws SQLException {
        insert("FIRST", roomId, CHECK_IN, CHECK_OUT, "CONFIRMED");
        updateStatus("FIRST", terminalStatus);
        insert("SECOND", roomId, CHECK_IN, CHECK_OUT, "CONFIRMED");

        assertEquals(2, scalar("SELECT count(*) FROM pms.reservations"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"CONFIRMED", "CHECKED_IN"})
    void shouldRejectReactivatingAnOverlappingReservation(String activeStatus) throws SQLException {
        // Direct SQL deliberately bypasses future application transition guards.
        insert("FIRST", roomId, CHECK_IN, CHECK_OUT, "CONFIRMED");
        insert("SECOND", roomId, CHECK_IN, CHECK_OUT, "CANCELLED");

        var error = assertThrows(PSQLException.class, () -> updateStatus("SECOND", activeStatus));

        assertExclusionViolation(error);
    }

    private void insert(String code, long room, LocalDate from, LocalDate to, String status)
            throws SQLException {
        try (var statement = connection.prepareStatement("""
                INSERT INTO pms.reservations
                    (confirmation_code, guest_id, room_id, rate_plan_id, check_in, check_out,
                     status, adults, total_price, price_breakdown, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 500.00, '[]'::jsonb, 'WEB')
                """)) {
            statement.setString(1, code);
            statement.setLong(2, guestId);
            statement.setLong(3, room);
            statement.setLong(4, ratePlanId);
            statement.setObject(5, from);
            statement.setObject(6, to);
            statement.setString(7, status);
            assertEquals(1, statement.executeUpdate());
        }
    }

    private void updateStatus(String code, String status) throws SQLException {
        try (var statement = connection.prepareStatement("""
                UPDATE pms.reservations SET status = ? WHERE confirmation_code = ?
                """)) {
            statement.setString(1, status);
            statement.setString(2, code);
            assertEquals(1, statement.executeUpdate());
        }
    }

    private static void assertExclusionViolation(PSQLException error) {
        assertEquals("23P01", error.getSQLState());
        assertNotNull(error.getServerErrorMessage());
        assertEquals("no_double_booking", error.getServerErrorMessage().getConstraint());
    }

    private long scalar(String sql) throws SQLException {
        try (var statement = connection.createStatement(); var rows = statement.executeQuery(sql)) {
            assertTrue(rows.next());
            return rows.getLong(1);
        }
    }
}
