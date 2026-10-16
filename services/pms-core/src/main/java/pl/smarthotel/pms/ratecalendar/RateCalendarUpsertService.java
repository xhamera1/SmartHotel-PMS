package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.pricing.PricingClient;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemResponse;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

/**
 * Separate bean so each refresh chunk runs in its own transaction
 * (self-invocation would bypass {@code @Transactional} on the same class).
 */
@Service
public class RateCalendarUpsertService {

    private static final Logger log = LoggerFactory.getLogger(RateCalendarUpsertService.class);
    private static final int MONEY_SCALE = 2;

    private final RateCalendarRepository rateCalendarRepository;
    private final RoomTypeRepository roomTypeRepository;
    private final PricingClient pricingClient;
    private final Clock clock;

    public RateCalendarUpsertService(
            RateCalendarRepository rateCalendarRepository,
            RoomTypeRepository roomTypeRepository,
            PricingClient pricingClient,
            Clock clock) {
        this.rateCalendarRepository = rateCalendarRepository;
        this.roomTypeRepository = roomTypeRepository;
        this.pricingClient = pricingClient;
        this.clock = clock;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public int upsertChunk(List<PricingQuoteItemRequest> items) {
        Optional<PricingQuotesResponse> response =
                pricingClient.fetchQuotes(new PricingQuotesRequest(UUID.randomUUID(), items));
        if (response.isEmpty() || response.get().items() == null) {
            log.warn("Pricing quotes failed for chunk of {} items — skipping", items.size());
            return 0;
        }
        return applyQuotes(response.get());
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public int applyQuotes(PricingQuotesResponse response) {
        if (response == null || response.items() == null || response.items().isEmpty()) {
            return 0;
        }

        Map<String, RoomTypeEntity> byCode = new HashMap<>();
        for (RoomTypeEntity rt : roomTypeRepository.findByActiveTrueOrderByCodeAsc()) {
            byCode.put(rt.getCode().toUpperCase(), rt);
        }

        int count = 0;
        String modelVersion = response.modelVersion();
        for (PricingQuoteItemResponse item : response.items()) {
            RoomTypeEntity roomType = byCode.get(item.roomTypeCode().toUpperCase());
            if (roomType == null) {
                continue;
            }
            Optional<RateCalendarEntity> existing =
                    rateCalendarRepository.findByRoomTypeIdAndDate(roomType.getId(), item.date());
            if (existing.isPresent() && existing.get().getSource() == PriceSource.MANUAL) {
                continue;
            }
            RateCalendarEntity entry = existing.orElseGet(RateCalendarEntity::new);
            entry.setRoomType(roomType);
            entry.setDate(item.date());
            BigDecimal price = item.price() != null
                    ? item.price().setScale(MONEY_SCALE, RoundingMode.HALF_UP)
                    : roomType.getBasePrice();
            entry.setPrice(price);
            entry.setSource(PriceSource.ML_MODEL);
            entry.setDemandIndicator((short) Math.max(0, Math.min(100, item.demandIndicator())));
            entry.setModelVersion(item.modelVersion() != null ? item.modelVersion() : modelVersion);
            entry.setFactors(item.factors());
            entry.setComputedAt(clock.instant());
            rateCalendarRepository.save(entry);
            count++;
        }
        return count;
    }
}
