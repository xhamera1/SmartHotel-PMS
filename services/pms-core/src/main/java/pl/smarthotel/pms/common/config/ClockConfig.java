package pl.smarthotel.pms.common.config;

import java.time.Clock;
import java.time.ZoneId;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.auditing.DateTimeProvider;

@Configuration
public class ClockConfig {

    public static final String HOTEL_ZONE_BEAN = "hotelZone";

    @Bean
    Clock clock() {
        return Clock.systemUTC();
    }

    /**
     * Hotel-local calendar zone for business dates (ADR-0009). Prefer this over
     * {@link ZoneId#systemDefault()} when deriving {@code LocalDate} "today".
     */
    @Bean(name = HOTEL_ZONE_BEAN)
    ZoneId hotelZone(@Value("${app.hotel.zone:Europe/Warsaw}") String zone) {
        return ZoneId.of(zone);
    }

    /** Makes JPA auditing timestamps come from the injectable {@link Clock}. */
    @Bean
    DateTimeProvider auditingDateTimeProvider(Clock clock) {
        return () -> java.util.Optional.of(clock.instant());
    }
}
