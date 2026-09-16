package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Pageable;
import pl.smarthotel.pms.common.exception.RoomNoLongerAvailableException;
import pl.smarthotel.pms.guests.GuestEntity;
import pl.smarthotel.pms.guests.GuestService;
import pl.smarthotel.pms.guests.GuestUpsertRequest;
import pl.smarthotel.pms.ratecalendar.NightlyBar;
import pl.smarthotel.pms.ratecalendar.PriceProvider;
import pl.smarthotel.pms.ratecalendar.PriceSource;
import pl.smarthotel.pms.rooms.RoomEntity;
import pl.smarthotel.pms.rooms.RoomStatus;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@ExtendWith(MockitoExtension.class)
class ReservationServiceExclusionConstraintTest {

    private static final ZoneId WARSAW = ZoneId.of("Europe/Warsaw");
    private static final LocalDate CHECK_IN = LocalDate.of(2026, 10, 3);
    private static final LocalDate CHECK_OUT = LocalDate.of(2026, 10, 5);

    @Mock
    private ReservationRepository reservationRepository;

    @Mock
    private RatePlanRepository ratePlanRepository;

    @Mock
    private RoomTypeRepository roomTypeRepository;

    @Mock
    private GuestService guestService;

    @Mock
    private PriceProvider priceProvider;

    @Mock
    private ConfirmationCodeGenerator confirmationCodeGenerator;

    private ReservationService service;

    @BeforeEach
    void setUp() {
        service = new ReservationService(
                reservationRepository,
                ratePlanRepository,
                roomTypeRepository,
                guestService,
                priceProvider,
                confirmationCodeGenerator,
                Clock.fixed(Instant.parse("2026-10-01T10:00:00Z"), WARSAW),
                WARSAW);
    }

    @Test
    void shouldTranslateExclusionConstraintToRoomNoLongerAvailable() {
        RoomTypeEntity roomType = roomType();
        RatePlanEntity plan = ratePlan();
        RoomEntity room = room(roomType);

        when(roomTypeRepository.findByCodeIgnoreCase("DLX")).thenReturn(Optional.of(roomType));
        when(ratePlanRepository.findByCodeIgnoreCase("FLEX")).thenReturn(Optional.of(plan));
        when(reservationRepository.findFreeRooms(eq(1L), eq(CHECK_IN), eq(CHECK_OUT), any(Pageable.class)))
                .thenReturn(List.of(room));
        when(guestService.findOrCreate(any(GuestUpsertRequest.class))).thenReturn(guest());
        when(priceProvider.resolveBars(eq(1L), any(), eq(CHECK_IN), eq(CHECK_OUT)))
                .thenReturn(List.of(new NightlyBar(CHECK_IN, new BigDecimal("420.00"), PriceSource.BASE)));
        when(confirmationCodeGenerator.next()).thenReturn("RACECODE");
        when(reservationRepository.saveAndFlush(any(ReservationEntity.class)))
                .thenThrow(new DataIntegrityViolationException(
                        "excluded", new SQLException("conflict", ExclusionConstraint.SQLSTATE)));

        assertThatThrownBy(() -> service.create(
                        new CreateReservationRequest(
                                "DLX",
                                "FLEX",
                                CHECK_IN,
                                CHECK_OUT,
                                (short) 2,
                                new GuestUpsertRequest("Jan", "Kowalski", "jan@example.com", null)),
                        ReservationSource.WEB))
                .isInstanceOf(RoomNoLongerAvailableException.class)
                .hasMessageContaining("DLX");
    }

    private static RoomTypeEntity roomType() {
        RoomTypeEntity rt = new RoomTypeEntity();
        try {
            var id = RoomTypeEntity.class.getDeclaredField("id");
            id.setAccessible(true);
            id.set(rt, 1L);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
        rt.setCode("DLX");
        rt.setName("Deluxe");
        rt.setCapacity((short) 3);
        rt.setBasePrice(new BigDecimal("420.00"));
        rt.setMinPrice(new BigDecimal("100.00"));
        rt.setMaxPrice(new BigDecimal("999.00"));
        rt.setActive(true);
        return rt;
    }

    private static RatePlanEntity ratePlan() {
        RatePlanEntity plan = new RatePlanEntity();
        plan.setCode("FLEX");
        plan.setName("Flexible");
        plan.setRefundable(true);
        plan.setBreakfastIncluded(false);
        plan.setPriceModifier(BigDecimal.ONE);
        plan.setActive(true);
        plan.setSortOrder((short) 10);
        return plan;
    }

    private static RoomEntity room(RoomTypeEntity type) {
        RoomEntity room = new RoomEntity();
        room.setRoomNumber("301");
        room.setRoomType(type);
        room.setStatus(RoomStatus.AVAILABLE);
        return room;
    }

    private static GuestEntity guest() {
        GuestEntity guest = new GuestEntity();
        guest.setFirstName("Jan");
        guest.setLastName("Kowalski");
        guest.setEmail("jan@example.com");
        return guest;
    }
}
