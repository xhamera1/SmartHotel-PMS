package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.config.ClockConfig;
import pl.smarthotel.pms.common.domain.OccupancyCalculator;
import pl.smarthotel.pms.pricing.PricingClient;
import pl.smarthotel.pms.pricing.PricingProperties;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemResponse;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;
import pl.smarthotel.pms.reservations.ReservationRepository;
import pl.smarthotel.pms.rooms.RoomRepository;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@Service
@Transactional(readOnly = true)
public class RateCalendarPriceProvider implements PriceProvider {

    private static final Logger log = LoggerFactory.getLogger(RateCalendarPriceProvider.class);
    private static final int MONEY_SCALE = 2;

    private final RateCalendarRepository rateCalendarRepository;
    private final RoomTypeRepository roomTypeRepository;
    private final RoomRepository roomRepository;
    private final ReservationRepository reservationRepository;
    private final PricingClient pricingClient;
    private final PricingProperties pricingProperties;
    private final RateCalendarUpsertService upsertService;
    private final Clock clock;
    private final ZoneId hotelZone;

    public RateCalendarPriceProvider(
            RateCalendarRepository rateCalendarRepository,
            RoomTypeRepository roomTypeRepository,
            RoomRepository roomRepository,
            ReservationRepository reservationRepository,
            PricingClient pricingClient,
            PricingProperties pricingProperties,
            RateCalendarUpsertService upsertService,
            Clock clock,
            @Qualifier(ClockConfig.HOTEL_ZONE_BEAN) ZoneId hotelZone) {
        this.rateCalendarRepository = rateCalendarRepository;
        this.roomTypeRepository = roomTypeRepository;
        this.roomRepository = roomRepository;
        this.reservationRepository = reservationRepository;
        this.pricingClient = pricingClient;
        this.pricingProperties = pricingProperties;
        this.upsertService = upsertService;
        this.clock = clock;
        this.hotelZone = hotelZone;
    }

    @Override
    public List<NightlyBar> resolveBars(
            long roomTypeId, BigDecimal basePrice, LocalDate checkIn, LocalDate checkOut) {
        Map<LocalDate, RateCalendarEntity> byDate = new HashMap<>();
        for (RateCalendarEntity entry :
                rateCalendarRepository.findByRoomTypeIdAndDateBetween(roomTypeId, checkIn, checkOut)) {
            byDate.put(entry.getDate(), entry);
        }

        List<NightlyBar> nights = new ArrayList<>();
        for (LocalDate night = checkIn; night.isBefore(checkOut); night = night.plusDays(1)) {
            RateCalendarEntity entry = byDate.get(night);
            if (entry != null) {
                nights.add(new NightlyBar(night, entry.getPrice(), entry.getSource()));
            } else {
                nights.add(resolveMissingNight(roomTypeId, basePrice, night));
            }
        }
        return nights;
    }

    private NightlyBar resolveMissingNight(long roomTypeId, BigDecimal basePrice, LocalDate night) {
        if (!pricingProperties.enabled()) {
            return new NightlyBar(night, basePrice, PriceSource.BASE);
        }

        Optional<RoomTypeEntity> roomTypeOpt = roomTypeRepository.findById(roomTypeId);
        if (roomTypeOpt.isEmpty()) {
            return new NightlyBar(night, basePrice, PriceSource.BASE_FALLBACK);
        }
        RoomTypeEntity roomType = roomTypeOpt.get();
        LocalDate today = LocalDate.now(clock.withZone(hotelZone));
        long sellable = roomRepository.countSellableByRoomTypeId(roomTypeId);
        long occupied = reservationRepository.countOccupiedRoomsForTypeOn(roomTypeId, night);
        int roomsRemaining = (int) Math.max(0, sellable - occupied);
        double occupancyRate = OccupancyCalculator.rate(occupied, sellable);
        int leadTimeDays = (int) Math.max(0, today.until(night).getDays());

        PricingQuoteItemRequest item = new PricingQuoteItemRequest(
                roomType.getCode(),
                night,
                roomType.getBasePrice(),
                roomType.getMinPrice(),
                roomType.getMaxPrice(),
                occupancyRate,
                roomsRemaining,
                leadTimeDays);

        try {
            Optional<PricingQuotesResponse> response =
                    pricingClient.fetchQuotesOnDemand(new PricingQuotesRequest(UUID.randomUUID(), List.of(item)));
            if (response.isPresent()
                    && response.get().items() != null
                    && !response.get().items().isEmpty()) {
                PricingQuoteItemResponse quoted = response.get().items().getFirst();
                BigDecimal price = quoted.price().setScale(MONEY_SCALE, RoundingMode.HALF_UP);
                try {
                    upsertService.applyQuotes(response.get());
                } catch (Exception cacheEx) {
                    log.debug("Could not cache on-demand quote: {}", cacheEx.toString());
                }
                return new NightlyBar(night, price, PriceSource.ML_MODEL);
            }
        } catch (Exception ex) {
            log.warn("On-demand pricing quote failed for {} {}: {}", roomType.getCode(), night, ex.toString());
        }
        return new NightlyBar(night, basePrice, PriceSource.BASE_FALLBACK);
    }
}
