package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import pl.smarthotel.pms.ratecalendar.NightlyBar;

/** Booking-time price snapshot math (ADR-0007): charged = round(BAR × modifier, 2) per night. */
public final class ReservationPricing {

    private static final int SCALE = 2;

    private ReservationPricing() {}

    public static List<PriceBreakdownLine> snapshot(List<NightlyBar> bars, BigDecimal priceModifier) {
        List<PriceBreakdownLine> lines = new ArrayList<>(bars.size());
        for (NightlyBar bar : bars) {
            BigDecimal price = bar.bar().multiply(priceModifier).setScale(SCALE, RoundingMode.HALF_UP);
            lines.add(new PriceBreakdownLine(bar.date(), price, bar.bar(), bar.priceSource()));
        }
        return List.copyOf(lines);
    }

    public static BigDecimal total(List<PriceBreakdownLine> lines) {
        BigDecimal sum = BigDecimal.ZERO;
        for (PriceBreakdownLine line : lines) {
            sum = sum.add(line.price());
        }
        return sum;
    }
}
