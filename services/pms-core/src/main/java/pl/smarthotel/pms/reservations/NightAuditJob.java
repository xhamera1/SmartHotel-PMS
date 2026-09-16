package pl.smarthotel.pms.reservations;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Closes the hotel day: CONFIRMED stays past check-in become NO_SHOW (T5).
 * Cron defaults to 00:05 Europe/Warsaw; overridable via {@code app.night-audit.cron}.
 */
@Component
public class NightAuditJob {

    private final ReservationService reservationService;

    public NightAuditJob(ReservationService reservationService) {
        this.reservationService = reservationService;
    }

    @Scheduled(cron = "${app.night-audit.cron:0 5 0 * * *}", zone = "${app.hotel.zone:Europe/Warsaw}")
    public void run() {
        reservationService.markNoShows();
    }
}
