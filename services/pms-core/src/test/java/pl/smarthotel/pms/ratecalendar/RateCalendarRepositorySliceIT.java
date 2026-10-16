package pl.smarthotel.pms.ratecalendar;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.postgresql.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import pl.smarthotel.pms.rooms.RoomTypeEntity;

@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class RateCalendarRepositorySliceIT {

    @Container
    static PostgreSQLContainer postgres = new PostgreSQLContainer("postgres:17")
            .withDatabaseName("pms_test")
            .withUsername("pms_test")
            .withPassword("pms_test");

    @DynamicPropertySource
    static void registerDatasource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.flyway.default-schema", () -> "pms");
        registry.add("spring.flyway.schemas", () -> "pms");
    }

    @Autowired
    private RateCalendarRepository repository;

    @Autowired
    private TestEntityManager em;

    private RoomTypeEntity persistedRoomType() {
        RoomTypeEntity rt = new RoomTypeEntity();
        rt.setCode("TST");
        rt.setName("Test Room");
        rt.setCapacity((short) 2);
        rt.setBasePrice(new BigDecimal("250.00"));
        rt.setMinPrice(new BigDecimal("180.00"));
        rt.setMaxPrice(new BigDecimal("450.00"));
        rt.setActive(true);
        return em.persistAndFlush(rt);
    }

    private RateCalendarEntity entry(RoomTypeEntity rt, LocalDate date, BigDecimal price, PriceSource source) {
        RateCalendarEntity e = new RateCalendarEntity();
        e.setRoomType(rt);
        e.setDate(date);
        e.setPrice(price);
        e.setSource(source);
        e.setComputedAt(Instant.now());
        return em.persistAndFlush(e);
    }

    @Test
    void findByRoomTypeIdAndDateBetween_returnsHalfOpenRange() {
        RoomTypeEntity rt = persistedRoomType();
        LocalDate d1 = LocalDate.of(2026, 10, 1);
        LocalDate d2 = LocalDate.of(2026, 10, 2);
        LocalDate d3 = LocalDate.of(2026, 10, 3);
        entry(rt, d1, new BigDecimal("300.00"), PriceSource.ML_MODEL);
        entry(rt, d2, new BigDecimal("320.00"), PriceSource.ML_MODEL);
        entry(rt, d3, new BigDecimal("310.00"), PriceSource.ML_MODEL);

        List<RateCalendarEntity> results = repository.findByRoomTypeIdAndDateBetween(rt.getId(), d1, d3);

        assertThat(results)
                .hasSize(2)
                .extracting(RateCalendarEntity::getDate)
                .containsExactlyInAnyOrder(d1, d2);
    }

    @Test
    void findByRoomTypeIdAndDate_findsExact() {
        RoomTypeEntity rt = persistedRoomType();
        LocalDate d = LocalDate.of(2026, 10, 15);
        entry(rt, d, new BigDecimal("420.00"), PriceSource.MANUAL);

        assertThat(repository.findByRoomTypeIdAndDate(rt.getId(), d)).isPresent();
        assertThat(repository.findByRoomTypeIdAndDate(rt.getId(), d.plusDays(1))).isEmpty();
    }

    @Test
    void findManualDatesForRoomType_filtersManualOnly() {
        RoomTypeEntity rt = persistedRoomType();
        LocalDate d1 = LocalDate.of(2026, 11, 1);
        LocalDate d2 = LocalDate.of(2026, 11, 2);
        LocalDate d3 = LocalDate.of(2026, 11, 3);
        entry(rt, d1, new BigDecimal("300.00"), PriceSource.MANUAL);
        entry(rt, d2, new BigDecimal("320.00"), PriceSource.ML_MODEL);
        entry(rt, d3, new BigDecimal("310.00"), PriceSource.MANUAL);

        List<LocalDate> manualDates = repository.findManualDatesForRoomType(rt.getId(), d1, d3.plusDays(1));
        assertThat(manualDates).containsExactlyInAnyOrder(d1, d3);
    }
}
