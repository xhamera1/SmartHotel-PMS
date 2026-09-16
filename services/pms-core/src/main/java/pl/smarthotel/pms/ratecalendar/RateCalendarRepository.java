package pl.smarthotel.pms.ratecalendar;

import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface RateCalendarRepository extends JpaRepository<RateCalendarEntity, Long> {

    /**
     * Calendar rows with {@code date} in {@code [fromInclusive, toExclusive)}.
     */
    @Query(
            """
            SELECT e FROM RateCalendarEntity e
            WHERE e.roomType.id = :roomTypeId
              AND e.date >= :fromInclusive
              AND e.date < :toExclusive
            """)
    List<RateCalendarEntity> findByRoomTypeIdAndDateBetween(
            @Param("roomTypeId") long roomTypeId,
            @Param("fromInclusive") LocalDate fromInclusive,
            @Param("toExclusive") LocalDate toExclusive);
}
