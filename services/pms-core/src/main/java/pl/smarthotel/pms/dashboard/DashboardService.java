package pl.smarthotel.pms.dashboard;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.config.ClockConfig;
import pl.smarthotel.pms.reservations.ReservationEntity;
import pl.smarthotel.pms.reservations.ReservationRepository;
import pl.smarthotel.pms.rooms.RoomRepository;
import pl.smarthotel.pms.rooms.RoomStatus;

@Service
@Transactional(readOnly = true)
public class DashboardService {

    private final ReservationRepository reservationRepository;
    private final RoomRepository roomRepository;
    private final Clock clock;
    private final ZoneId hotelZone;

    public DashboardService(
            ReservationRepository reservationRepository,
            RoomRepository roomRepository,
            Clock clock,
            @Qualifier(ClockConfig.HOTEL_ZONE_BEAN) ZoneId hotelZone) {
        this.reservationRepository = reservationRepository;
        this.roomRepository = roomRepository;
        this.clock = clock;
        this.hotelZone = hotelZone;
    }

    public DashboardKpisResponse kpis() {
        LocalDate today = LocalDate.ofInstant(clock.instant(), hotelZone);
        long occupied = reservationRepository.countOccupiedRoomsOn(today);
        long sellable = roomRepository.countByStatusNot(RoomStatus.OUT_OF_SERVICE);
        long arrivals = reservationRepository.countArrivalsOn(today);
        long departures = reservationRepository.countDeparturesOn(today);
        LocalDate monthStart = today.with(TemporalAdjusters.firstDayOfMonth());
        LocalDate monthEnd = monthStart.plusMonths(1);
        BigDecimal mtd = reservationRepository.sumMtdRevenue(monthStart, monthEnd);
        return DashboardKpisResponse.of(today, occupied, sellable, arrivals, departures, mtd);
    }

    public DashboardTimeseriesResponse timeseries(int days) {
        int window = Math.min(Math.max(days, 1), 90);
        LocalDate to = LocalDate.ofInstant(clock.instant(), hotelZone);
        LocalDate from = to.minusDays(window - 1L);
        long sellable = roomRepository.countByStatusNot(RoomStatus.OUT_OF_SERVICE);
        List<ReservationEntity> overlapping =
                reservationRepository.findForOccupancyWindow(from, to.plusDays(1));

        List<DashboardDayPoint> points = new ArrayList<>(window);
        for (LocalDate day = from; !day.isAfter(to); day = day.plusDays(1)) {
            long occupied = 0;
            BigDecimal nightRevenue = BigDecimal.ZERO;
            for (ReservationEntity reservation : overlapping) {
                if (!reservation.getCheckIn().isAfter(day) && reservation.getCheckOut().isAfter(day)) {
                    occupied++;
                    long nights = ChronoUnit.DAYS.between(reservation.getCheckIn(), reservation.getCheckOut());
                    if (nights > 0 && reservation.getTotalPrice() != null) {
                        nightRevenue = nightRevenue.add(reservation
                                .getTotalPrice()
                                .divide(BigDecimal.valueOf(nights), 4, RoundingMode.HALF_UP));
                    }
                }
            }
            BigDecimal occupancy = sellable == 0
                    ? BigDecimal.ZERO.setScale(4, RoundingMode.HALF_UP)
                    : BigDecimal.valueOf(occupied)
                            .divide(BigDecimal.valueOf(sellable), 4, RoundingMode.HALF_UP);
            BigDecimal adr = occupied == 0
                    ? BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP)
                    : nightRevenue.divide(BigDecimal.valueOf(occupied), 2, RoundingMode.HALF_UP);
            points.add(new DashboardDayPoint(day, occupancy, adr, occupied, sellable));
        }
        return new DashboardTimeseriesResponse(from, to, "PLN", List.copyOf(points));
    }
}
