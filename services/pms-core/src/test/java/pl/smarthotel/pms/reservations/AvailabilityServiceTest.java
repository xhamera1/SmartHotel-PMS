package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.ratecalendar.NightlyBar;
import pl.smarthotel.pms.ratecalendar.PriceProvider;
import pl.smarthotel.pms.ratecalendar.PriceSource;

@ExtendWith(MockitoExtension.class)
class AvailabilityServiceTest {

    private static final LocalDate CHECK_IN = LocalDate.of(2026, 10, 3);
    private static final LocalDate CHECK_OUT = LocalDate.of(2026, 10, 5);

    @Mock
    private AvailabilityRepository availabilityRepository;

    @Mock
    private PriceProvider priceProvider;

    @Mock
    private RatePlanRepository ratePlanRepository;

    private AvailabilityService service;

    @BeforeEach
    void setUp() {
        service = new AvailabilityService(availabilityRepository, priceProvider, ratePlanRepository);
    }

    @Test
    void shouldRejectCheckOutNotAfterCheckIn() {
        assertThatThrownBy(() -> service.search(CHECK_IN, CHECK_IN, 2))
                .isInstanceOf(ApplicationException.class)
                .hasMessageContaining("checkOut");
        verify(availabilityRepository, never()).findAvailableRoomTypes(any(), any(), anyInt());
    }

    @Test
    void shouldRejectNonPositivePartySize() {
        assertThatThrownBy(() -> service.search(CHECK_IN, CHECK_OUT, 0))
                .isInstanceOf(ApplicationException.class)
                .hasMessageContaining("guests");
    }

    @Test
    void shouldReturnEmptyWhenNoRoomsFree() {
        when(availabilityRepository.findAvailableRoomTypes(CHECK_IN, CHECK_OUT, 2)).thenReturn(List.of());

        AvailabilityResponse response = service.search(CHECK_IN, CHECK_OUT, 2);

        assertThat(response.roomTypes()).isEmpty();
        assertThat(response.currency()).isEqualTo("PLN");
        verify(priceProvider, never()).resolveBars(anyLong(), any(), any(), any());
    }

    @Test
    void shouldGroupByRoomTypeWithCalendarPricesAndDerivedRatePlanTotals() {
        when(availabilityRepository.findAvailableRoomTypes(CHECK_IN, CHECK_OUT, 2))
                .thenReturn(List.of(new AvailableRoomTypeRow(
                        10L, "DLX", "Deluxe Double", (short) 3, new BigDecimal("420.00"), 2L)));
        when(priceProvider.resolveBars(eq(10L), eq(new BigDecimal("420.00")), eq(CHECK_IN), eq(CHECK_OUT)))
                .thenReturn(List.of(
                        new NightlyBar(CHECK_IN, new BigDecimal("612.00"), PriceSource.ML_MODEL),
                        new NightlyBar(
                                CHECK_IN.plusDays(1), new BigDecimal("580.00"), PriceSource.ML_MODEL)));
        when(ratePlanRepository.findByActiveTrueOrderBySortOrderAsc())
                .thenReturn(List.of(
                        ratePlan("FLEX", "Flexible", true, false, "1.0000", 10),
                        ratePlan("NONREF", "Non-refundable", false, false, "0.9000", 20)));

        AvailabilityResponse response = service.search(CHECK_IN, CHECK_OUT, 2);

        assertThat(response.checkIn()).isEqualTo(CHECK_IN);
        assertThat(response.checkOut()).isEqualTo(CHECK_OUT);
        assertThat(response.guests()).isEqualTo(2);
        assertThat(response.roomTypes()).hasSize(1);

        AvailableRoomTypeAvailability dlx = response.roomTypes().getFirst();
        assertThat(dlx.code()).isEqualTo("DLX");
        assertThat(dlx.roomsLeft()).isEqualTo(2);
        assertThat(dlx.nights())
                .extracting(NightAvailability::priceSource)
                .containsExactly(PriceSource.ML_MODEL, PriceSource.ML_MODEL);
        assertThat(dlx.nights())
                .extracting(NightAvailability::bar)
                .containsExactly(new BigDecimal("612.00"), new BigDecimal("580.00"));

        // Rate plans ordered by sort_order: FLEX (10) then NONREF (20)
        assertThat(dlx.ratePlans()).extracting(RatePlanQuote::code).containsExactly("FLEX", "NONREF");
        // FLEX: 612 + 580 = 1192.00; NONREF: round(612*0.9)+round(580*0.9) = 550.80 + 522.00
        assertThat(dlx.ratePlans().get(0).totalPrice()).isEqualByComparingTo("1192.00");
        assertThat(dlx.ratePlans().get(1).totalPrice()).isEqualByComparingTo("1072.80");
        assertThat(dlx.ratePlans().get(1).refundable()).isFalse();
    }

    @Test
    void shouldFlagBaseFallbackNightsInResponse() {
        when(availabilityRepository.findAvailableRoomTypes(CHECK_IN, CHECK_OUT, 1))
                .thenReturn(List.of(new AvailableRoomTypeRow(
                        1L, "STD", "Standard", (short) 2, new BigDecimal("250.00"), 5L)));
        when(priceProvider.resolveBars(anyLong(), any(), any(), any()))
                .thenReturn(List.of(
                        new NightlyBar(CHECK_IN, new BigDecimal("250.00"), PriceSource.BASE),
                        new NightlyBar(
                                CHECK_IN.plusDays(1), new BigDecimal("250.00"), PriceSource.BASE)));
        when(ratePlanRepository.findByActiveTrueOrderBySortOrderAsc())
                .thenReturn(List.of(ratePlan("FLEX", "Flexible", true, false, "1.0000", 10)));

        AvailabilityResponse response = service.search(CHECK_IN, CHECK_OUT, 1);

        assertThat(response.roomTypes().getFirst().nights())
                .allMatch(n -> n.priceSource() == PriceSource.BASE);
        assertThat(response.roomTypes().getFirst().ratePlans().getFirst().totalPrice())
                .isEqualByComparingTo("500.00");
    }

    private static RatePlanEntity ratePlan(
            String code,
            String name,
            boolean refundable,
            boolean breakfast,
            String modifier,
            int sortOrder) {
        RatePlanEntity entity = new RatePlanEntity();
        entity.setCode(code);
        entity.setName(name);
        entity.setRefundable(refundable);
        entity.setBreakfastIncluded(breakfast);
        entity.setPriceModifier(new BigDecimal(modifier));
        entity.setActive(true);
        entity.setSortOrder((short) sortOrder);
        return entity;
    }
}
