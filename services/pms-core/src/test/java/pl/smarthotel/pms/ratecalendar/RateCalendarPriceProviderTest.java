package pl.smarthotel.pms.ratecalendar;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
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
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import pl.smarthotel.pms.pricing.PricingClient;
import pl.smarthotel.pms.pricing.PricingProperties;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemResponse;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;
import pl.smarthotel.pms.reservations.ReservationRepository;
import pl.smarthotel.pms.rooms.RoomRepository;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@ExtendWith(MockitoExtension.class)
class RateCalendarPriceProviderTest {

    private static final ZoneId ZONE = ZoneId.of("Europe/Warsaw");
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-10-01T10:00:00Z"), ZONE);

    @Mock
    private RateCalendarRepository rateCalendarRepository;

    @Mock
    private RoomTypeRepository roomTypeRepository;

    @Mock
    private RoomRepository roomRepository;

    @Mock
    private ReservationRepository reservationRepository;

    @Mock
    private PricingClient pricingClient;

    @Mock
    private RateCalendarUpsertService upsertService;

    private RateCalendarPriceProvider providerDisabled;
    private RateCalendarPriceProvider providerEnabled;

    @BeforeEach
    void setUp() {
        PricingProperties disabled = props(false);
        PricingProperties enabled = props(true);
        providerDisabled = new RateCalendarPriceProvider(
                rateCalendarRepository,
                roomTypeRepository,
                roomRepository,
                reservationRepository,
                pricingClient,
                disabled,
                upsertService,
                CLOCK,
                ZONE);
        providerEnabled = new RateCalendarPriceProvider(
                rateCalendarRepository,
                roomTypeRepository,
                roomRepository,
                reservationRepository,
                pricingClient,
                enabled,
                upsertService,
                CLOCK,
                ZONE);
    }

    @Test
    void shouldUseCalendarPriceWhenPresent() {
        LocalDate night = LocalDate.of(2026, 10, 3);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(
                        eq(1L), eq(night), eq(LocalDate.of(2026, 10, 4))))
                .thenReturn(List.of(entry(night, "612.00", PriceSource.ML_MODEL)));

        List<NightlyBar> nights = providerDisabled.resolveBars(
                1L, new BigDecimal("420.00"), night, LocalDate.of(2026, 10, 4));

        assertThat(nights).containsExactly(new NightlyBar(night, new BigDecimal("612.00"), PriceSource.ML_MODEL));
        verify(pricingClient, never()).fetchQuotes(any());
    }

    @Test
    void shouldFallBackToBasePriceWhenCalendarMissingAndPricingDisabled() {
        LocalDate checkIn = LocalDate.of(2026, 10, 3);
        LocalDate checkOut = LocalDate.of(2026, 10, 5);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(eq(2L), eq(checkIn), eq(checkOut)))
                .thenReturn(List.of());

        List<NightlyBar> nights =
                providerDisabled.resolveBars(2L, new BigDecimal("250.00"), checkIn, checkOut);

        assertThat(nights)
                .containsExactly(
                        new NightlyBar(checkIn, new BigDecimal("250.00"), PriceSource.BASE),
                        new NightlyBar(
                                checkIn.plusDays(1), new BigDecimal("250.00"), PriceSource.BASE));
        verify(pricingClient, never()).fetchQuotes(any());
    }

    @Test
    void shouldUseBaseFallbackWhenOnDemandQuoteFails() {
        LocalDate night = LocalDate.of(2026, 10, 3);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(
                        eq(3L), eq(night), eq(LocalDate.of(2026, 10, 4))))
                .thenReturn(List.of());
        when(roomTypeRepository.findById(3L)).thenReturn(Optional.of(roomType(3L, "STD")));
        when(roomRepository.countSellableByRoomTypeId(3L)).thenReturn(10L);
        when(reservationRepository.countOccupiedRoomsForTypeOn(3L, night)).thenReturn(2L);
        when(pricingClient.fetchQuotes(any(PricingQuotesRequest.class))).thenReturn(Optional.empty());

        List<NightlyBar> nights =
                providerEnabled.resolveBars(3L, new BigDecimal("250.00"), night, LocalDate.of(2026, 10, 4));

        assertThat(nights)
                .containsExactly(new NightlyBar(night, new BigDecimal("250.00"), PriceSource.BASE_FALLBACK));
    }

    @Test
    void shouldUseMlPriceWhenOnDemandQuoteSucceeds() {
        LocalDate night = LocalDate.of(2026, 10, 3);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(
                        eq(4L), eq(night), eq(LocalDate.of(2026, 10, 4))))
                .thenReturn(List.of());
        when(roomTypeRepository.findById(4L)).thenReturn(Optional.of(roomType(4L, "DLX")));
        when(roomRepository.countSellableByRoomTypeId(4L)).thenReturn(5L);
        when(reservationRepository.countOccupiedRoomsForTypeOn(4L, night)).thenReturn(1L);
        when(pricingClient.fetchQuotes(any(PricingQuotesRequest.class)))
                .thenReturn(Optional.of(new PricingQuotesResponse(
                        "v1",
                        List.of(new PricingQuoteItemResponse(
                                "DLX",
                                night,
                                new BigDecimal("480.00"),
                                1.1,
                                55,
                                java.util.Map.of(),
                                "v1")))));
        when(upsertService.applyQuotes(any())).thenReturn(1);

        List<NightlyBar> nights =
                providerEnabled.resolveBars(4L, new BigDecimal("420.00"), night, LocalDate.of(2026, 10, 4));

        assertThat(nights)
                .containsExactly(new NightlyBar(night, new BigDecimal("480.00"), PriceSource.ML_MODEL));
    }

    @Test
    void shouldMixCalendarAndBaseFallbackAcrossStay() {
        LocalDate checkIn = LocalDate.of(2026, 10, 3);
        LocalDate checkOut = LocalDate.of(2026, 10, 5);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(anyLong(), any(), any()))
                .thenReturn(List.of(entry(checkIn, "300.00", PriceSource.MANUAL)));

        List<NightlyBar> nights =
                providerDisabled.resolveBars(3L, new BigDecimal("250.00"), checkIn, checkOut);

        assertThat(nights)
                .containsExactly(
                        new NightlyBar(checkIn, new BigDecimal("300.00"), PriceSource.MANUAL),
                        new NightlyBar(
                                checkIn.plusDays(1), new BigDecimal("250.00"), PriceSource.BASE));
    }

    private static PricingProperties props(boolean enabled) {
        return new PricingProperties(enabled, "http://localhost:9", "k", 500, 1000, 1000, 30, 50, 2000);
    }

    private static RateCalendarEntity entry(LocalDate date, String price, PriceSource source) {
        RateCalendarEntity entity = new RateCalendarEntity();
        entity.setDate(date);
        entity.setPrice(new BigDecimal(price));
        entity.setSource(source);
        return entity;
    }

    private static RoomTypeEntity roomType(long id, String code) {
        RoomTypeEntity rt = new RoomTypeEntity();
        rt.setCode(code);
        rt.setName(code);
        rt.setCapacity((short) 2);
        rt.setBasePrice(new BigDecimal("350.00"));
        rt.setMinPrice(new BigDecimal("200.00"));
        rt.setMaxPrice(new BigDecimal("800.00"));
        // id is generated — use reflection-free approach via repository returning entity with known code
        try {
            var field = RoomTypeEntity.class.getDeclaredField("id");
            field.setAccessible(true);
            field.set(rt, id);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
        return rt;
    }
}
