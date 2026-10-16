package pl.smarthotel.pms.ratecalendar;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import pl.smarthotel.pms.pricing.PricingProperties;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemRequest;
import pl.smarthotel.pms.reservations.ReservationRepository;
import pl.smarthotel.pms.rooms.RoomRepository;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@ExtendWith(MockitoExtension.class)
class RateCalendarRefreshJobTest {

    private static final ZoneId ZONE = ZoneId.of("Europe/Warsaw");
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-10-01T01:00:00Z"), ZONE);

    @Mock
    private RateCalendarRepository rateCalendarRepository;

    @Mock
    private RoomTypeRepository roomTypeRepository;

    @Mock
    private RoomRepository roomRepository;

    @Mock
    private ReservationRepository reservationRepository;

    @Mock
    private RateCalendarUpsertService upsertService;

    private RateCalendarService service;
    private RateCalendarRefreshJob job;

    @BeforeEach
    void setUp() {
        PricingProperties props =
                new PricingProperties(true, "http://localhost:9", "k", 500, 1000, 1000, 5, 3, 2000);
        service = new RateCalendarService(
                rateCalendarRepository,
                roomTypeRepository,
                roomRepository,
                reservationRepository,
                upsertService,
                props,
                CLOCK,
                ZONE);
        job = new RateCalendarRefreshJob(service);
    }

    @Test
    void refreshSkipsManualDatesAndUpsertsOtherNights() {
        RoomTypeEntity std = roomType("STD");
        when(roomTypeRepository.findByActiveTrueOrderByCodeAsc()).thenReturn(List.of(std));
        when(roomRepository.countSellableByRoomTypeId(1L)).thenReturn(10L);
        when(reservationRepository.countOccupiedRoomsForTypeOn(eq(1L), any())).thenReturn(2L);
        LocalDate today = LocalDate.of(2026, 10, 1);
        when(rateCalendarRepository.findManualDatesForRoomType(1L, today, today.plusDays(5)))
                .thenReturn(List.of(today.plusDays(1))); // 2026-10-02 MANUAL
        when(upsertService.upsertChunk(anyList())).thenAnswer(inv -> {
            List<?> items = inv.getArgument(0);
            return items.size();
        });

        int updated = service.refreshFromPricing();

        ArgumentCaptor<List<PricingQuoteItemRequest>> captor = ArgumentCaptor.forClass(List.class);
        verify(upsertService, times(2)).upsertChunk(captor.capture());
        List<PricingQuoteItemRequest> all = captor.getAllValues().stream()
                .flatMap(List::stream)
                .toList();
        Set<LocalDate> dates = all.stream().map(PricingQuoteItemRequest::date).collect(Collectors.toSet());
        assertThat(dates).doesNotContain(today.plusDays(1));
        assertThat(dates).contains(today, today.plusDays(2), today.plusDays(3), today.plusDays(4));
        assertThat(updated).isEqualTo(4);
    }

    @Test
    void refreshContinuesAfterChunkFailure() {
        RoomTypeEntity std = roomType("STD");
        when(roomTypeRepository.findByActiveTrueOrderByCodeAsc()).thenReturn(List.of(std));
        when(roomRepository.countSellableByRoomTypeId(1L)).thenReturn(4L);
        when(reservationRepository.countOccupiedRoomsForTypeOn(eq(1L), any())).thenReturn(0L);
        LocalDate today = LocalDate.of(2026, 10, 1);
        when(rateCalendarRepository.findManualDatesForRoomType(1L, today, today.plusDays(5)))
                .thenReturn(List.of());
        when(upsertService.upsertChunk(anyList()))
                .thenThrow(new RuntimeException("pricing down"))
                .thenReturn(2);

        int updated = service.refreshFromPricing();

        verify(upsertService, times(2)).upsertChunk(anyList());
        assertThat(updated).isEqualTo(2);
    }

    @Test
    void scheduledJobDelegatesToService() {
        RoomTypeEntity std = roomType("STD");
        when(roomTypeRepository.findByActiveTrueOrderByCodeAsc()).thenReturn(List.of(std));
        when(roomRepository.countSellableByRoomTypeId(1L)).thenReturn(2L);
        when(reservationRepository.countOccupiedRoomsForTypeOn(eq(1L), any())).thenReturn(0L);
        LocalDate today = LocalDate.of(2026, 10, 1);
        when(rateCalendarRepository.findManualDatesForRoomType(1L, today, today.plusDays(5)))
                .thenReturn(List.of());
        when(upsertService.upsertChunk(anyList())).thenReturn(5);

        job.run();

        verify(upsertService, times(2)).upsertChunk(anyList());
    }

    private static RoomTypeEntity roomType(String code) {
        RoomTypeEntity rt = new RoomTypeEntity();
        try {
            var field = RoomTypeEntity.class.getDeclaredField("id");
            field.setAccessible(true);
            field.set(rt, 1L);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
        rt.setCode(code);
        rt.setName(code);
        rt.setCapacity((short) 2);
        rt.setBasePrice(new BigDecimal("350.00"));
        rt.setMinPrice(new BigDecimal("200.00"));
        rt.setMaxPrice(new BigDecimal("800.00"));
        rt.setActive(true);
        return rt;
    }
}
