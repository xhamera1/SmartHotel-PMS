package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.config.ClockConfig;
import pl.smarthotel.pms.common.domain.OccupancyCalculator;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.pricing.PricingProperties;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemRequest;
import pl.smarthotel.pms.reservations.ReservationRepository;
import pl.smarthotel.pms.rooms.RoomRepository;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@Service
@Transactional(readOnly = true)
public class RateCalendarService {

    private static final Logger log = LoggerFactory.getLogger(RateCalendarService.class);
    private static final int MONEY_SCALE = 2;

    private final RateCalendarRepository rateCalendarRepository;
    private final RoomTypeRepository roomTypeRepository;
    private final RoomRepository roomRepository;
    private final ReservationRepository reservationRepository;
    private final RateCalendarUpsertService upsertService;
    private final PricingProperties pricingProperties;
    private final Clock clock;
    private final ZoneId hotelZone;

    public RateCalendarService(
            RateCalendarRepository rateCalendarRepository,
            RoomTypeRepository roomTypeRepository,
            RoomRepository roomRepository,
            ReservationRepository reservationRepository,
            RateCalendarUpsertService upsertService,
            PricingProperties pricingProperties,
            Clock clock,
            @Qualifier(ClockConfig.HOTEL_ZONE_BEAN) ZoneId hotelZone) {
        this.rateCalendarRepository = rateCalendarRepository;
        this.roomTypeRepository = roomTypeRepository;
        this.roomRepository = roomRepository;
        this.reservationRepository = reservationRepository;
        this.upsertService = upsertService;
        this.pricingProperties = pricingProperties;
        this.clock = clock;
        this.hotelZone = hotelZone;
    }

    public RateCalendarResponse getCalendar(String roomTypeCode, LocalDate from, LocalDate to) {
        if (from == null || to == null) {
            throw ApplicationException.badRequest("from and to are required");
        }
        if (!from.isBefore(to)) {
            throw ApplicationException.badRequest("from must be strictly before to");
        }
        RoomTypeEntity roomType = requireRoomType(roomTypeCode);
        Map<LocalDate, RateCalendarEntity> byDate = new HashMap<>();
        for (RateCalendarEntity entry :
                rateCalendarRepository.findByRoomTypeIdAndDateBetween(roomType.getId(), from, to)) {
            byDate.put(entry.getDate(), entry);
        }

        List<RateCalendarDayResponse> days = new ArrayList<>();
        for (LocalDate night = from; night.isBefore(to); night = night.plusDays(1)) {
            RateCalendarEntity entry = byDate.get(night);
            if (entry != null) {
                days.add(new RateCalendarDayResponse(
                        night,
                        entry.getPrice(),
                        entry.getSource(),
                        entry.getDemandIndicator(),
                        true));
            } else {
                days.add(new RateCalendarDayResponse(
                        night, roomType.getBasePrice(), PriceSource.BASE, null, false));
            }
        }
        return new RateCalendarResponse(roomType.getCode(), days);
    }

    @Transactional
    public RateCalendarDayResponse putManualOverride(
            String roomTypeCode, LocalDate date, ManualRateOverrideRequest request) {
        RoomTypeEntity roomType = requireRoomType(roomTypeCode);
        BigDecimal price = request.price().setScale(MONEY_SCALE, RoundingMode.HALF_UP);
        if (price.compareTo(roomType.getMinPrice()) < 0 || price.compareTo(roomType.getMaxPrice()) > 0) {
            throw ApplicationException.badRequest(
                    "Price must be within ["
                            + roomType.getMinPrice()
                            + ", "
                            + roomType.getMaxPrice()
                            + "] for "
                            + roomType.getCode());
        }

        RateCalendarEntity entry = rateCalendarRepository
                .findByRoomTypeIdAndDate(roomType.getId(), date)
                .orElseGet(RateCalendarEntity::new);
        entry.setRoomType(roomType);
        entry.setDate(date);
        entry.setPrice(price);
        entry.setSource(PriceSource.MANUAL);
        entry.setDemandIndicator(null);
        entry.setModelVersion(null);
        entry.setFactors(null);
        entry.setComputedAt(clock.instant());
        RateCalendarEntity saved = rateCalendarRepository.save(entry);
        return new RateCalendarDayResponse(
                saved.getDate(), saved.getPrice(), saved.getSource(), saved.getDemandIndicator(), true);
    }

    @Transactional
    public void deleteManualOverride(String roomTypeCode, LocalDate date) {
        RoomTypeEntity roomType = requireRoomType(roomTypeCode);
        RateCalendarEntity entry = rateCalendarRepository
                .findByRoomTypeIdAndDate(roomType.getId(), date)
                .orElseThrow(() -> ApplicationException.notFound(
                        "No rate calendar entry for " + roomType.getCode() + " on " + date));
        if (entry.getSource() != PriceSource.MANUAL) {
            throw ApplicationException.conflict(
                    "Only MANUAL overrides can be deleted (found " + entry.getSource() + ")");
        }
        rateCalendarRepository.delete(entry);
    }

    /**
     * Pull ML quotes from pricing-service and upsert non-MANUAL rate calendar rows.
     * Suspends the class-level read-only transaction so each chunk can write.
     *
     * @return number of nights upserted
     */
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public int refreshFromPricing() {
        if (!pricingProperties.enabled()) {
            log.info("Pricing disabled — skipping rate calendar refresh");
            return 0;
        }

        LocalDate today = LocalDate.now(clock.withZone(hotelZone));
        LocalDate horizonEnd = today.plusDays(pricingProperties.refreshHorizonDays());
        List<RoomTypeEntity> roomTypes = roomTypeRepository.findByActiveTrueOrderByCodeAsc();
        int chunkSize = pricingProperties.refreshChunkSize();
        int upserted = 0;

        List<PricingQuoteItemRequest> batch = new ArrayList<>(chunkSize);
        for (RoomTypeEntity roomType : roomTypes) {
            long sellable = roomRepository.countSellableByRoomTypeId(roomType.getId());
            Set<LocalDate> manualDates = new HashSet<>(rateCalendarRepository.findManualDatesForRoomType(
                    roomType.getId(), today, horizonEnd));

            for (LocalDate night = today; night.isBefore(horizonEnd); night = night.plusDays(1)) {
                if (manualDates.contains(night)) {
                    continue;
                }
                long occupied = reservationRepository.countOccupiedRoomsForTypeOn(roomType.getId(), night);
                int roomsRemaining = (int) Math.max(0, sellable - occupied);
                double occupancyRate = OccupancyCalculator.rate(occupied, sellable);
                int leadTimeDays = (int) Math.max(0, today.until(night).getDays());

                batch.add(new PricingQuoteItemRequest(
                        roomType.getCode(),
                        night,
                        roomType.getBasePrice(),
                        roomType.getMinPrice(),
                        roomType.getMaxPrice(),
                        occupancyRate,
                        roomsRemaining,
                        leadTimeDays));

                if (batch.size() >= chunkSize) {
                    try {
                        upserted += upsertService.upsertChunk(batch);
                    } catch (Exception ex) {
                        log.warn("Chunk upsert failed ({} items): {}", batch.size(), ex.toString());
                    }
                    batch = new ArrayList<>(chunkSize);
                }
            }
        }
        if (!batch.isEmpty()) {
            try {
                upserted += upsertService.upsertChunk(batch);
            } catch (Exception ex) {
                log.warn("Final chunk upsert failed ({} items): {}", batch.size(), ex.toString());
            }
        }
        log.info("Rate calendar refresh complete: {} nights upserted", upserted);
        return upserted;
    }

    private RoomTypeEntity requireRoomType(String roomTypeCode) {
        return roomTypeRepository
                .findByCodeIgnoreCase(roomTypeCode.trim())
                .orElseThrow(() -> ApplicationException.notFound("Room type not found: " + roomTypeCode));
    }
}
