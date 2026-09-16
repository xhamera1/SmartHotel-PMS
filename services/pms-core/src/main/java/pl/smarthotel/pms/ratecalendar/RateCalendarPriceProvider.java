package pl.smarthotel.pms.ratecalendar;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class RateCalendarPriceProvider implements PriceProvider {

    private final RateCalendarRepository rateCalendarRepository;

    public RateCalendarPriceProvider(RateCalendarRepository rateCalendarRepository) {
        this.rateCalendarRepository = rateCalendarRepository;
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
                nights.add(new NightlyBar(night, basePrice, PriceSource.BASE));
            }
        }
        return nights;
    }
}
