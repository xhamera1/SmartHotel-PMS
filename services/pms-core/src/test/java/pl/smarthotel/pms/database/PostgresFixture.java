package pl.smarthotel.pms.database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import org.flywaydb.core.Flyway;
import org.testcontainers.postgresql.PostgreSQLContainer;

final class PostgresFixture {
    private PostgresFixture() {}

    static PostgreSQLContainer postgres() {
        return new PostgreSQLContainer("postgres:17")
                .withDatabaseName("pms_test")
                .withUsername("pms_test")
                .withPassword("pms_test");
    }

    static Connection connect(PostgreSQLContainer postgres) throws SQLException {
        return DriverManager.getConnection(
                postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword());
    }

    static Flyway flyway(PostgreSQLContainer postgres, boolean includeSeeds) {
        String[] locations = includeSeeds
                ? new String[] {"classpath:db/migration", "classpath:db/seed"}
                : new String[] {"classpath:db/migration"};
        return Flyway.configure()
                .dataSource(postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword())
                .defaultSchema("pms")
                .schemas("pms")
                .locations(locations)
                .load();
    }
}
