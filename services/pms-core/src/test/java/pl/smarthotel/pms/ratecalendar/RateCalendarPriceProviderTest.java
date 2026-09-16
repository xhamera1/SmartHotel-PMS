package pl.smarthotel.pms.ratecalendar;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class RateCalendarPriceProviderTest {

    @Mock
    private RateCalendarRepository rateCalendarRepository;

    private RateCalendarPriceProvider provider;

    @BeforeEach
    void setUp() {
        provider = new RateCalendarPriceProvider(rateCalendarRepository);
    }

    @Test
    void shouldUseCalendarPriceWhenPresent() {
        LocalDate night = LocalDate.of(2026, 10, 3);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(
                        eq(1L), eq(night), eq(LocalDate.of(2026, 10, 4))))
                .thenReturn(List.of(entry(night, "612.00", PriceSource.ML_MODEL)));

        List<NightlyBar> nights = provider.resolveBars(
                1L, new BigDecimal("420.00"), night, LocalDate.of(2026, 10, 4));

        assertThat(nights).containsExactly(new NightlyBar(night, new BigDecimal("612.00"), PriceSource.ML_MODEL));
    }

    @Test
    void shouldFallBackToBasePriceWhenCalendarMissing() {
        LocalDate checkIn = LocalDate.of(2026, 10, 3);
        LocalDate checkOut = LocalDate.of(2026, 10, 5);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(eq(2L), eq(checkIn), eq(checkOut)))
                .thenReturn(List.of());

        List<NightlyBar> nights =
                provider.resolveBars(2L, new BigDecimal("250.00"), checkIn, checkOut);

        assertThat(nights)
                .containsExactly(
                        new NightlyBar(checkIn, new BigDecimal("250.00"), PriceSource.BASE),
                        new NightlyBar(
                                checkIn.plusDays(1), new BigDecimal("250.00"), PriceSource.BASE));
    }

    @Test
    void shouldMixCalendarAndBaseFallbackAcrossStay() {
        LocalDate checkIn = LocalDate.of(2026, 10, 3);
        LocalDate checkOut = LocalDate.of(2026, 10, 5);
        when(rateCalendarRepository.findByRoomTypeIdAndDateBetween(anyLong(), any(), any()))
                .thenReturn(List.of(entry(checkIn, "300.00", PriceSource.MANUAL)));

        List<NightlyBar> nights =
                provider.resolveBars(3L, new BigDecimal("250.00"), checkIn, checkOut);

        assertThat(nights)
                .containsExactly(
                        new NightlyBar(checkIn, new BigDecimal("300.00"), PriceSource.MANUAL),
                        new NightlyBar(
                                checkIn.plusDays(1), new BigDecimal("250.00"), PriceSource.BASE));
    }

    private static RateCalendarEntity entry(LocalDate date, String price, PriceSource source) {
        RateCalendarEntity entity = new RateCalendarEntity();
        entity.setDate(date);
        entity.setPrice(new BigDecimal(price));
        entity.setSource(source);
        return entity;
    }
}
