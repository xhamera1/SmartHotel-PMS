package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Pageable;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.exception.RoomNoLongerAvailableException;
import pl.smarthotel.pms.common.web.ProblemTypes;
import pl.smarthotel.pms.guests.GuestEntity;
import pl.smarthotel.pms.guests.GuestService;
import pl.smarthotel.pms.guests.GuestUpsertRequest;
import pl.smarthotel.pms.ratecalendar.NightlyBar;
import pl.smarthotel.pms.ratecalendar.PriceProvider;
import pl.smarthotel.pms.ratecalendar.PriceSource;
import pl.smarthotel.pms.rooms.RoomEntity;
import pl.smarthotel.pms.rooms.RoomStatus;
import pl.smarthotel.pms.rooms.RoomTypeEntity;

@ExtendWith(MockitoExtension.class)
class ReservationServiceTest {

    private static final ZoneId WARSAW = ZoneId.of("Europe/Warsaw");
    private static final LocalDate CHECK_IN = LocalDate.of(2026, 10, 3);
    private static final LocalDate CHECK_OUT = LocalDate.of(2026, 10, 5);

    @Mock
    private ReservationRepository reservationRepository;

    @Mock
    private RatePlanRepository ratePlanRepository;

    @Mock
    private pl.smarthotel.pms.rooms.RoomTypeRepository roomTypeRepository;

    @Mock
    private GuestService guestService;

    @Mock
    private PriceProvider priceProvider;

    @Mock
    private ConfirmationCodeGenerator confirmationCodeGenerator;

    private ReservationService service;

    @BeforeEach
    void setUp() {
        // Business "today" = 2026-10-01 (before check-in)
        Clock clock = Clock.fixed(Instant.parse("2026-10-01T10:00:00Z"), WARSAW);
        service = new ReservationService(
                reservationRepository,
                ratePlanRepository,
                roomTypeRepository,
                guestService,
                priceProvider,
                confirmationCodeGenerator,
                clock,
                WARSAW);
    }

    @Test
    void shouldCreateConfirmedReservationWithAssignedRoomAndPriceSnapshot() {
        RoomTypeEntity roomType = roomType("DLX", 3, "420.00");
        RatePlanEntity plan = ratePlan("FLEX", true, "1.0000");
        RoomEntity room = room(roomType, "301");
        GuestEntity guest = guest("jan@example.com");

        when(roomTypeRepository.findByCodeIgnoreCase("DLX")).thenReturn(Optional.of(roomType));
        when(ratePlanRepository.findByCodeIgnoreCase("FLEX")).thenReturn(Optional.of(plan));
        when(reservationRepository.findFreeRooms(eq(roomType.getId()), eq(CHECK_IN), eq(CHECK_OUT), any()))
                .thenReturn(List.of(room));
        when(guestService.findOrCreate(any(GuestUpsertRequest.class))).thenReturn(guest);
        when(priceProvider.resolveBars(eq(1L), eq(new BigDecimal("420.00")), eq(CHECK_IN), eq(CHECK_OUT)))
                .thenReturn(List.of(
                        new NightlyBar(CHECK_IN, new BigDecimal("420.00"), PriceSource.BASE),
                        new NightlyBar(CHECK_IN.plusDays(1), new BigDecimal("420.00"), PriceSource.BASE)));
        when(confirmationCodeGenerator.next()).thenReturn("K7NR4PWM");
        when(reservationRepository.saveAndFlush(any(ReservationEntity.class)))
                .thenAnswer(inv -> inv.getArgument(0));

        CreateReservationRequest request = new CreateReservationRequest(
                "DLX",
                "FLEX",
                CHECK_IN,
                CHECK_OUT,
                (short) 2,
                new GuestUpsertRequest("Jan", "Kowalski", "jan@example.com", null));

        ReservationResponse response = service.create(request, ReservationSource.WEB);

        assertThat(response.confirmationCode()).isEqualTo("K7NR4PWM");
        assertThat(response.status()).isEqualTo(ReservationStatus.CONFIRMED);
        assertThat(response.roomType()).isEqualTo("DLX");
        assertThat(response.totalPrice()).isEqualByComparingTo("840.00");
        assertThat(response.priceBreakdown()).hasSize(2);

        ArgumentCaptor<ReservationEntity> captor = ArgumentCaptor.forClass(ReservationEntity.class);
        verify(reservationRepository).saveAndFlush(captor.capture());
        assertThat(captor.getValue().getRoom()).isSameAs(room);
        assertThat(captor.getValue().getSource()).isEqualTo(ReservationSource.WEB);
    }

    @Test
    void shouldRejectCreateWhenNoFreeRoom() {
        RoomTypeEntity roomType = roomType("DLX", 3, "420.00");
        when(roomTypeRepository.findByCodeIgnoreCase("DLX")).thenReturn(Optional.of(roomType));
        when(ratePlanRepository.findByCodeIgnoreCase("FLEX"))
                .thenReturn(Optional.of(ratePlan("FLEX", true, "1.0000")));
        when(reservationRepository.findFreeRooms(anyLong(), any(), any(), any(Pageable.class)))
                .thenReturn(List.of());

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
                .extracting(ex -> ((ApplicationException) ex).getProblemType())
                .isEqualTo(ProblemTypes.ROOM_NO_LONGER_AVAILABLE);
    }

    @Test
    void shouldRejectGuestCancelOnNonRefundablePlan() {
        ReservationEntity reservation = confirmedReservation(ratePlan("NONREF", false, "0.9000"));
        when(reservationRepository.findByConfirmationCodeAndGuestEmailIgnoreCase("ABCD1234", "jan@example.com"))
                .thenReturn(Optional.of(reservation));

        assertThatThrownBy(() -> service.cancelByGuest("ABCD1234", "jan@example.com"))
                .isInstanceOf(ApplicationException.ConflictException.class)
                .extracting(ex -> ((ApplicationException) ex).getProblemType())
                .isEqualTo(ProblemTypes.RATE_PLAN_NOT_REFUNDABLE);
    }

    @Test
    void shouldRejectGuestCancelOnOrAfterCheckInDate() {
        // today = 2026-10-03 == check_in
        Clock clock = Clock.fixed(Instant.parse("2026-10-03T08:00:00Z"), WARSAW);
        service = new ReservationService(
                reservationRepository,
                ratePlanRepository,
                roomTypeRepository,
                guestService,
                priceProvider,
                confirmationCodeGenerator,
                clock,
                WARSAW);
        ReservationEntity reservation = confirmedReservation(ratePlan("FLEX", true, "1.0000"));
        when(reservationRepository.findByConfirmationCodeAndGuestEmailIgnoreCase("ABCD1234", "jan@example.com"))
                .thenReturn(Optional.of(reservation));

        assertThatThrownBy(() -> service.cancelByGuest("ABCD1234", "jan@example.com"))
                .isInstanceOf(ApplicationException.ConflictException.class)
                .extracting(ex -> ((ApplicationException) ex).getProblemType())
                .isEqualTo(ProblemTypes.ILLEGAL_STATE_TRANSITION);
    }

    @Test
    void shouldAllowGuestCancelBeforeCheckInWhenRefundable() {
        ReservationEntity reservation = confirmedReservation(ratePlan("FLEX", true, "1.0000"));
        when(reservationRepository.findByConfirmationCodeAndGuestEmailIgnoreCase("ABCD1234", "jan@example.com"))
                .thenReturn(Optional.of(reservation));
        when(reservationRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ReservationResponse response = service.cancelByGuest("ABCD1234", "jan@example.com");

        assertThat(response.status()).isEqualTo(ReservationStatus.CANCELLED);
    }

    @Test
    void shouldRejectCheckInBeforeArrivalDate() {
        ReservationEntity reservation = confirmedReservation(ratePlan("FLEX", true, "1.0000"));
        reservation.setId(99L);
        when(reservationRepository.findByIdForUpdate(99L)).thenReturn(Optional.of(reservation));

        assertThatThrownBy(() -> service.checkIn(99L))
                .isInstanceOf(ApplicationException.ConflictException.class)
                .extracting(ex -> ((ApplicationException) ex).getProblemType())
                .isEqualTo(ProblemTypes.ILLEGAL_STATE_TRANSITION);
    }

    @Test
    void shouldMarkNoShowsWhenBusinessDateAfterCheckIn() {
        Clock clock = Clock.fixed(Instant.parse("2026-10-04T02:00:00Z"), WARSAW);
        service = new ReservationService(
                reservationRepository,
                ratePlanRepository,
                roomTypeRepository,
                guestService,
                priceProvider,
                confirmationCodeGenerator,
                clock,
                WARSAW);

        ReservationEntity stale = confirmedReservation(ratePlan("FLEX", true, "1.0000"));
        when(reservationRepository.findConfirmedWithCheckInBefore(LocalDate.of(2026, 10, 4)))
                .thenReturn(List.of(stale));
        when(reservationRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        int marked = service.markNoShows(LocalDate.of(2026, 10, 4));

        assertThat(marked).isEqualTo(1);
        assertThat(stale.getStatus()).isEqualTo(ReservationStatus.NO_SHOW);
    }

    private ReservationEntity confirmedReservation(RatePlanEntity plan) {
        RoomTypeEntity roomType = roomType("DLX", 3, "420.00");
        ReservationEntity entity = new ReservationEntity();
        entity.setConfirmationCode("ABCD1234");
        entity.setStatus(ReservationStatus.CONFIRMED);
        entity.setCheckIn(CHECK_IN);
        entity.setCheckOut(CHECK_OUT);
        entity.setAdults((short) 2);
        entity.setTotalPrice(new BigDecimal("840.00"));
        entity.setCurrency("PLN");
        entity.setPriceBreakdown(List.of());
        entity.setSource(ReservationSource.WEB);
        entity.setRatePlan(plan);
        entity.setRoom(room(roomType, "301"));
        entity.setGuest(guest("jan@example.com"));
        return entity;
    }

    private static RoomTypeEntity roomType(String code, int capacity, String base) {
        RoomTypeEntity rt = new RoomTypeEntity();
        // id via reflection-free: set through a package helper — use anonymous subclass field
        try {
            var id = RoomTypeEntity.class.getDeclaredField("id");
            id.setAccessible(true);
            id.set(rt, 1L);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
        rt.setCode(code);
        rt.setName(code);
        rt.setCapacity((short) capacity);
        rt.setBasePrice(new BigDecimal(base));
        rt.setMinPrice(new BigDecimal("100.00"));
        rt.setMaxPrice(new BigDecimal("999.00"));
        rt.setActive(true);
        return rt;
    }

    private static RatePlanEntity ratePlan(String code, boolean refundable, String modifier) {
        RatePlanEntity plan = new RatePlanEntity();
        plan.setCode(code);
        plan.setName(code);
        plan.setRefundable(refundable);
        plan.setBreakfastIncluded(false);
        plan.setPriceModifier(new BigDecimal(modifier));
        plan.setActive(true);
        plan.setSortOrder((short) 10);
        return plan;
    }

    private static RoomEntity room(RoomTypeEntity type, String number) {
        RoomEntity room = new RoomEntity();
        room.setRoomNumber(number);
        room.setRoomType(type);
        room.setStatus(RoomStatus.AVAILABLE);
        return room;
    }

    private static GuestEntity guest(String email) {
        GuestEntity guest = new GuestEntity();
        guest.setFirstName("Jan");
        guest.setLastName("Kowalski");
        guest.setEmail(email);
        return guest;
    }
}
