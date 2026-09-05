package pl.smarthotel.pms.database;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.SQLException;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

@Testcontainers
class PmsMigrationIT {
    // A new container for each test proves migration from an empty database.
    @Container
    final PostgreSQLContainer postgres = PostgresFixture.postgres();

    @Test
    void shouldMigrateEmptyDatabaseWithoutDevSeedsAndAllowRerun() throws SQLException {
        var flyway = PostgresFixture.flyway(postgres, false);

        assertEquals(1, flyway.migrate().migrationsExecuted);
        assertEquals(Set.of("staff_users", "room_types", "rooms", "rate_plans", "guests",
                "reservations", "rate_calendar", "flyway_schema_history"), tableNames());
        assertEquals(1, scalar("SELECT count(*) FROM pg_extension WHERE extname = 'btree_gist'"));
        assertEquals(1, scalar("""
                SELECT count(*) FROM pg_constraint
                WHERE conrelid = 'pms.reservations'::regclass
                  AND conname = 'no_double_booking' AND contype = 'x'
                """));
        assertEquals(1, scalar("""
                SELECT count(*) FROM information_schema.columns
                WHERE table_schema = 'pms' AND table_name = 'reservations'
                  AND column_name = 'stay' AND is_generated = 'ALWAYS'
                """));
        assertEquals(0, scalar("SELECT count(*) FROM pms.staff_users"));
        assertEquals(0, scalar("SELECT count(*) FROM pms.rooms"));
        assertEquals(0, scalar("SELECT count(*) FROM pms.rate_plans"));

        assertEquals(0, flyway.migrate().migrationsExecuted);
        flyway.validate();
        // Flyway also records its own schema-creation marker on a pristine DB.
        assertEquals(1, scalar("""
                SELECT count(*) FROM pms.flyway_schema_history WHERE success AND type = 'SQL'
                """));
    }

    @Test
    void shouldApplyDevSeedsOnceWhenExplicitlyEnabled() throws SQLException {
        var flyway = PostgresFixture.flyway(postgres, true);

        assertEquals(2, flyway.migrate().migrationsExecuted);
        assertSeedCounts();
        assertEquals(0, flyway.migrate().migrationsExecuted);
        flyway.validate();
        assertSeedCounts();
        assertEquals(2, scalar("""
                SELECT count(*) FROM pms.flyway_schema_history WHERE success AND type = 'SQL'
                """));
    }

    @Test
    void shouldMigrateWithPreexistingInfraSchemasAndPublicExtension() throws SQLException {
        try (var connection = PostgresFixture.connect(postgres);
                var statement = connection.createStatement()) {
            statement.execute("CREATE SCHEMA pms");
            statement.execute("CREATE SCHEMA pricing");
            statement.execute("CREATE EXTENSION btree_gist WITH SCHEMA public");
        }

        var flyway = PostgresFixture.flyway(postgres, false);
        assertEquals(1, flyway.migrate().migrationsExecuted);
        assertEquals(0, flyway.migrate().migrationsExecuted);
        flyway.validate();
        assertEquals(0, scalar("""
                SELECT count(*) FROM information_schema.tables WHERE table_schema = 'pricing'
                """));
    }

    private void assertSeedCounts() throws SQLException {
        assertEquals(3, scalar("SELECT count(*) FROM pms.room_types"));
        assertEquals(35, scalar("SELECT count(*) FROM pms.rooms"));
        assertEquals(3, scalar("SELECT count(*) FROM pms.rate_plans"));
        assertEquals(2, scalar("SELECT count(*) FROM pms.staff_users"));
    }

    private Set<String> tableNames() throws SQLException {
        try (var connection = PostgresFixture.connect(postgres);
                var statement = connection.createStatement();
                var rows = statement.executeQuery("""
                        SELECT table_name FROM information_schema.tables WHERE table_schema = 'pms'
                        """)) {
            Set<String> names = new HashSet<>();
            while (rows.next()) {
                names.add(rows.getString(1));
            }
            return names;
        }
    }

    private long scalar(String sql) throws SQLException {
        try (var connection = PostgresFixture.connect(postgres);
                var statement = connection.createStatement();
                var rows = statement.executeQuery(sql)) {
            assertTrue(rows.next());
            return rows.getLong(1);
        }
    }
}
