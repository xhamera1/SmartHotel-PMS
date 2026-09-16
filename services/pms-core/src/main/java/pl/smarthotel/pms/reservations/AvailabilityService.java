package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.ratecalendar.NightlyBar;
import pl.smarthotel.pms.ratecalendar.PriceProvider;

@Service
@Transactional(readOnly = true)
public class AvailabilityService {

    private static final String CURRENCY = "PLN";
    private static final int MONEY_SCALE = 2;

    private final AvailabilityRepository availabilityRepository;
    private final PriceProvider priceProvider;
    private final RatePlanRepository ratePlanRepository;

    public AvailabilityService(
            AvailabilityRepository availabilityRepository,
            PriceProvider priceProvider,
            RatePlanRepository ratePlanRepository) {
        this.availabilityRepository = availabilityRepository;
        this.priceProvider = priceProvider;
        this.ratePlanRepository = ratePlanRepository;
    }

    public AvailabilityResponse search(LocalDate checkIn, LocalDate checkOut, int guests) {
        validate(checkIn, checkOut, guests);

        List<RatePlanEntity> ratePlans = ratePlanRepository.findByActiveTrueOrderBySortOrderAsc();
        List<AvailableRoomTypeRow> freeTypes =
                availabilityRepository.findAvailableRoomTypes(checkIn, checkOut, guests);

        List<AvailableRoomTypeAvailability> roomTypes = new ArrayList<>(freeTypes.size());
        for (AvailableRoomTypeRow row : freeTypes) {
            List<NightlyBar> bars =
                    priceProvider.resolveBars(row.roomTypeId(), row.basePrice(), checkIn, checkOut);
            roomTypes.add(toAvailability(row, bars, ratePlans));
        }

        return new AvailabilityResponse(checkIn, checkOut, guests, CURRENCY, roomTypes);
    }

    private static void validate(LocalDate checkIn, LocalDate checkOut, int guests) {
        if (checkIn == null || checkOut == null) {
            throw ApplicationException.badRequest("checkIn and checkOut are required");
        }
        if (!checkOut.isAfter(checkIn)) {
            throw ApplicationException.badRequest("checkOut must be after checkIn");
        }
        if (guests < 1 || guests > 10) {
            throw ApplicationException.badRequest("guests must be between 1 and 10");
        }
    }

    private static AvailableRoomTypeAvailability toAvailability(
            AvailableRoomTypeRow row, List<NightlyBar> bars, List<RatePlanEntity> ratePlans) {
        List<NightAvailability> nights = bars.stream()
                .map(b -> new NightAvailability(b.date(), b.bar(), b.priceSource()))
                .toList();
        List<RatePlanQuote> quotes = ratePlans.stream()
                .map(plan -> new RatePlanQuote(
                        plan.getCode(),
                        plan.getName(),
                        plan.isRefundable(),
                        plan.isBreakfastIncluded(),
                        totalForPlan(bars, plan.getPriceModifier())))
                .toList();
        return new AvailableRoomTypeAvailability(
                row.code(), row.name(), row.capacity(), row.roomsLeft(), nights, quotes);
    }

    /** Σ round(bar × modifier, 2) over nights — ADR-0007. */
    static BigDecimal totalForPlan(List<NightlyBar> bars, BigDecimal priceModifier) {
        BigDecimal total = BigDecimal.ZERO;
        for (NightlyBar night : bars) {
            total = total.add(night.bar().multiply(priceModifier).setScale(MONEY_SCALE, RoundingMode.HALF_UP));
        }
        return total;
    }
}
