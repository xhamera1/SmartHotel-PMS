package pl.smarthotel.pms.dashboard;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.TemporalAdjusters;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.config.ClockConfig;
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
}
