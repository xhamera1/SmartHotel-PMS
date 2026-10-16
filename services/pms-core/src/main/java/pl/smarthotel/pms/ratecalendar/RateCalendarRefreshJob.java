package pl.smarthotel.pms.ratecalendar;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix = "app.pricing", name = "enabled", havingValue = "true", matchIfMissing = true)
public class RateCalendarRefreshJob {

    private static final Logger log = LoggerFactory.getLogger(RateCalendarRefreshJob.class);

    private final RateCalendarService rateCalendarService;

    public RateCalendarRefreshJob(RateCalendarService rateCalendarService) {
        this.rateCalendarService = rateCalendarService;
    }

    @Scheduled(
            cron = "${app.rate-refresh.cron:0 0 3 * * *}",
            zone = "${app.hotel.zone:Europe/Warsaw}")
    public void run() {
        log.info("Starting scheduled rate-calendar refresh");
        try {
            int updated = rateCalendarService.refreshFromPricing();
            log.info("Scheduled rate-calendar refresh finished: {} nights", updated);
        } catch (Exception ex) {
            log.warn("Scheduled rate-calendar refresh failed: {}", ex.toString());
        }
    }
}
