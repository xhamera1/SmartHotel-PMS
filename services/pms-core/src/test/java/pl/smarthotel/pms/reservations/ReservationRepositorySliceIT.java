package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.domain.Pageable;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.postgresql.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import pl.smarthotel.pms.guests.GuestEntity;
import pl.smarthotel.pms.rooms.RoomEntity;
import pl.smarthotel.pms.rooms.RoomStatus;
import pl.smarthotel.pms.rooms.RoomTypeEntity;

@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class ReservationRepositorySliceIT {

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
    private ReservationRepository repository;

    @Autowired
    private TestEntityManager em;

    private RoomTypeEntity roomType;
    private RoomEntity room1;
    private RoomEntity room2;
    private GuestEntity guest;

    @BeforeEach
    void setUp() {
        roomType = new RoomTypeEntity();
        roomType.setCode("SLC");
        roomType.setName("Slice Test");
        roomType.setCapacity((short) 2);
        roomType.setBasePrice(new BigDecimal("250.00"));
        roomType.setMinPrice(new BigDecimal("180.00"));
        roomType.setMaxPrice(new BigDecimal("450.00"));
        roomType.setActive(true);
        em.persistAndFlush(roomType);

        room1 = new RoomEntity();
        room1.setRoomNumber("SL01");
        room1.setRoomType(roomType);
        room1.setFloor((short) 1);
        room1.setStatus(RoomStatus.AVAILABLE);
        em.persistAndFlush(room1);

        room2 = new RoomEntity();
        room2.setRoomNumber("SL02");
        room2.setRoomType(roomType);
        room2.setFloor((short) 1);
        room2.setStatus(RoomStatus.AVAILABLE);
        em.persistAndFlush(room2);

        guest = new GuestEntity();
        guest.setFirstName("Slice");
        guest.setLastName("Test");
        guest.setEmail("slice-test@example.com");
        em.persistAndFlush(guest);
    }

    private ReservationEntity reservation(
            RoomEntity room, LocalDate checkIn, LocalDate checkOut, ReservationStatus status) {
        ReservationEntity r = new ReservationEntity();
        r.setConfirmationCode("SLC" + checkIn.getDayOfMonth() + room.getRoomNumber());
        r.setGuest(guest);
        r.setRoom(room);
        r.setCheckIn(checkIn);
        r.setCheckOut(checkOut);
        r.setStatus(status);
        r.setAdults((short) 2);
        r.setTotalPrice(new BigDecimal("500.00"));
        r.setCurrency("PLN");
        r.setPriceBreakdown(List.of());
        r.setSource(ReservationSource.ADMIN);
        return em.persistAndFlush(r);
    }

    @Test
    void findFreeRooms_excludesOccupied() {
        LocalDate ci = LocalDate.of(2026, 12, 1);
        LocalDate co = LocalDate.of(2026, 12, 3);
        reservation(room1, ci, co, ReservationStatus.CONFIRMED);

        var free = repository.findFreeRooms(roomType.getId(), ci, co, Pageable.unpaged());
        assertThat(free).extracting(RoomEntity::getRoomNumber).containsExactly("SL02");
    }

    @Test
    void countOccupiedRoomsOn_countsActiveStatuses() {
        LocalDate ci = LocalDate.of(2026, 12, 10);
        LocalDate co = LocalDate.of(2026, 12, 12);
        reservation(room1, ci, co, ReservationStatus.CONFIRMED);
        reservation(room2, ci, co, ReservationStatus.CANCELLED);

        assertThat(repository.countOccupiedRoomsOn(ci)).isEqualTo(1);
        assertThat(repository.countOccupiedRoomsOn(co)).isEqualTo(0);
    }

    @Test
    void countOccupiedRoomsForTypeOn_filtersByRoomType() {
        LocalDate ci = LocalDate.of(2026, 12, 15);
        LocalDate co = LocalDate.of(2026, 12, 17);
        reservation(room1, ci, co, ReservationStatus.CONFIRMED);

        assertThat(repository.countOccupiedRoomsForTypeOn(roomType.getId(), ci)).isEqualTo(1);
        assertThat(repository.countOccupiedRoomsForTypeOn(roomType.getId(), co)).isEqualTo(0);
    }

    @Test
    void findConfirmedWithCheckInBefore_findsOnlyConfirmed() {
        LocalDate yesterday = LocalDate.of(2026, 12, 1);
        LocalDate today = LocalDate.of(2026, 12, 2);
        reservation(room1, yesterday, yesterday.plusDays(2), ReservationStatus.CONFIRMED);
        reservation(room2, today, today.plusDays(2), ReservationStatus.CONFIRMED);

        var result = repository.findConfirmedWithCheckInBefore(today);
        assertThat(result).hasSize(1);
        assertThat(result.getFirst().getRoom().getRoomNumber()).isEqualTo("SL01");
    }

    @Test
    void sumMtdRevenue_sumsActiveReservations() {
        LocalDate ci = LocalDate.of(2026, 11, 5);
        reservation(room1, ci, ci.plusDays(2), ReservationStatus.CONFIRMED);
        reservation(room2, ci.plusDays(1), ci.plusDays(3), ReservationStatus.CANCELLED);

        BigDecimal revenue = repository.sumMtdRevenue(
                LocalDate.of(2026, 11, 1), LocalDate.of(2026, 12, 1));
        assertThat(revenue).isEqualByComparingTo("500.00");
    }
}
