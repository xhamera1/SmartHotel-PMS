package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@Service
@Transactional(readOnly = true)
public class RateCalendarService {

    private static final int MONEY_SCALE = 2;

    private final RateCalendarRepository rateCalendarRepository;
    private final RoomTypeRepository roomTypeRepository;
    private final Clock clock;

    public RateCalendarService(
            RateCalendarRepository rateCalendarRepository,
            RoomTypeRepository roomTypeRepository,
            Clock clock) {
        this.rateCalendarRepository = rateCalendarRepository;
        this.roomTypeRepository = roomTypeRepository;
        this.clock = clock;
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

    private RoomTypeEntity requireRoomType(String roomTypeCode) {
        return roomTypeRepository
                .findByCodeIgnoreCase(roomTypeCode.trim())
                .orElseThrow(() -> ApplicationException.notFound("Room type not found: " + roomTypeCode));
    }
}
