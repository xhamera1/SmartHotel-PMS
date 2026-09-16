package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import jakarta.persistence.EntityManager;
import jakarta.persistence.OptimisticLockException;
import java.time.LocalDate;
import java.util.Map;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import pl.smarthotel.pms.database.PostgresFixture;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ReservationPersistenceIT {

    @Container
    static final PostgreSQLContainer POSTGRES = PostgresFixture.postgres();

    @DynamicPropertySource
    static void registerDataSource(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("spring.jpa.properties.hibernate.generate_statistics", () -> "true");
    }

    @Autowired
    private TestRestTemplate rest;

    @Autowired
    private EntityManager entityManager;

    @Autowired
    private TransactionTemplate transactionTemplate;

    @Autowired
    private ReservationRepository reservationRepository;

    @Test
    void optimisticLockBumpsVersionOnConcurrentUpdate() {
        LocalDate in = LocalDate.now().plusDays(90);
        ReservationResponse created = rest.postForEntity(
                        "/api/v1/reservations",
                        Map.of(
                                "roomTypeCode",
                                "STD",
                                "ratePlanCode",
                                "FLEX",
                                "checkIn",
                                in.toString(),
                                "checkOut",
                                in.plusDays(1).toString(),
                                "adults",
                                2,
                                "guest",
                                Map.of(
                                        "firstName",
                                        "Opt",
                                        "lastName",
                                        "Lock",
                                        "email",
                                        "opt.lock@example.com")),
                        ReservationResponse.class)
                .getBody();

        ReservationEntity first = transactionTemplate.execute(status -> {
            ReservationEntity entity = reservationRepository.findByIdForUpdate(created.id()).orElseThrow();
            entityManager.detach(entity);
            return entity;
        });
        ReservationEntity second = transactionTemplate.execute(status -> {
            ReservationEntity entity = reservationRepository.findByIdForUpdate(created.id()).orElseThrow();
            entityManager.detach(entity);
            return entity;
        });

        assertThat(first.getVersion()).isEqualTo(second.getVersion());

        transactionTemplate.executeWithoutResult(status -> {
            ReservationEntity managed = reservationRepository.findByIdForUpdate(created.id()).orElseThrow();
            managed.setAdults((short) 1);
            reservationRepository.saveAndFlush(managed);
        });

        assertThatThrownBy(() -> transactionTemplate.executeWithoutResult(status -> {
                    entityManager.merge(second);
                    second.setAdults((short) 2);
                    reservationRepository.saveAndFlush(second);
                }))
                .isInstanceOfAny(ObjectOptimisticLockingFailureException.class, OptimisticLockException.class);
    }

    @Test
    void adminListUsesEntityGraphWithoutNPlusOneExplosion() {
        LocalDate in = LocalDate.now().plusDays(100);
        for (int i = 0; i < 3; i++) {
            rest.postForEntity(
                    "/api/v1/reservations",
                    Map.of(
                            "roomTypeCode",
                            "STD",
                            "ratePlanCode",
                            "FLEX",
                            "checkIn",
                            in.plusDays(i * 3).toString(),
                            "checkOut",
                            in.plusDays(i * 3 + 1).toString(),
                            "adults",
                            2,
                            "guest",
                            Map.of(
                                    "firstName",
                                    "N",
                                    "lastName",
                                    "Plus" + i,
                                    "email",
                                    "nplus" + i + "@example.com")),
                    ReservationResponse.class);
        }

        Statistics stats = entityManager.getEntityManagerFactory()
                .unwrap(SessionFactory.class)
                .getStatistics();
        stats.clear();

        transactionTemplate.executeWithoutResult(status -> {
            var page = reservationRepository.searchAdmin(
                    null, null, null, null, org.springframework.data.domain.PageRequest.of(0, 20));
            page.forEach(r -> {
                r.getGuest().getEmail();
                r.getRoom().getRoomNumber();
                r.getRoom().getRoomType().getCode();
                r.getRatePlan().getCode();
            });
        });

        assertThat(stats.getPrepareStatementCount())
                .as("EntityGraph should keep query count small for admin list")
                .isLessThanOrEqualTo(5);
    }
}
