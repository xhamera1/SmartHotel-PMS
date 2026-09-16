package pl.smarthotel.pms.common.config;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.auditing.DateTimeProvider;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.database.PostgresFixture;

@Testcontainers
@SpringBootTest
@ActiveProfiles("test")
class ClockAndAuditingIT {

    @Container
    static final PostgreSQLContainer POSTGRES = PostgresFixture.postgres();

    @DynamicPropertySource
    static void registerDataSource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }

    @Autowired
    private Clock clock;

    @Autowired
    @Qualifier(ClockConfig.HOTEL_ZONE_BEAN)
    private ZoneId hotelZone;

    @Autowired
    private DateTimeProvider auditingDateTimeProvider;

    @Test
    void clockAndHotelZoneAreWiredForBusinessTime() {
        assertThat(clock.getZone()).isEqualTo(ZoneId.of("UTC"));
        assertThat(hotelZone).isEqualTo(ZoneId.of("Europe/Warsaw"));
        assertThat(auditingDateTimeProvider.getNow()).isPresent();
        assertThat(auditingDateTimeProvider.getNow().orElseThrow()).isInstanceOf(Instant.class);
    }
}
