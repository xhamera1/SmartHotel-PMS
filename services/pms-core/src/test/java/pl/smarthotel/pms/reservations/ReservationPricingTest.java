package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;
import pl.smarthotel.pms.ratecalendar.NightlyBar;
import pl.smarthotel.pms.ratecalendar.PriceSource;

class ReservationPricingTest {

    @Test
    void shouldSnapshotDerivedNightlyPricesAndTotal() {
        LocalDate d1 = LocalDate.of(2026, 10, 3);
        LocalDate d2 = LocalDate.of(2026, 10, 4);
        List<NightlyBar> bars = List.of(
                new NightlyBar(d1, new BigDecimal("612.00"), PriceSource.ML_MODEL),
                new NightlyBar(d2, new BigDecimal("580.00"), PriceSource.ML_MODEL));

        List<PriceBreakdownLine> lines =
                ReservationPricing.snapshot(bars, new BigDecimal("0.9000"));

        assertThat(lines)
                .containsExactly(
                        new PriceBreakdownLine(
                                d1, new BigDecimal("550.80"), new BigDecimal("612.00"), PriceSource.ML_MODEL),
                        new PriceBreakdownLine(
                                d2, new BigDecimal("522.00"), new BigDecimal("580.00"), PriceSource.ML_MODEL));
        assertThat(ReservationPricing.total(lines)).isEqualByComparingTo("1072.80");
    }

    @Test
    void shouldPreserveBaseFallbackSourceInSnapshot() {
        LocalDate night = LocalDate.of(2026, 12, 1);
        List<PriceBreakdownLine> lines = ReservationPricing.snapshot(
                List.of(new NightlyBar(night, new BigDecimal("250.00"), PriceSource.BASE)),
                BigDecimal.ONE);

        assertThat(lines.getFirst().priceSource()).isEqualTo(PriceSource.BASE);
        assertThat(lines.getFirst().price()).isEqualByComparingTo("250.00");
        assertThat(lines.getFirst().barPrice()).isEqualByComparingTo("250.00");
    }
}
