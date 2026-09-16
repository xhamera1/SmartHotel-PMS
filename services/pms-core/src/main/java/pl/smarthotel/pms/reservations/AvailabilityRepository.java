package pl.smarthotel.pms.reservations;

import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;
import org.springframework.data.repository.query.Param;
import pl.smarthotel.pms.rooms.RoomEntity;

public interface AvailabilityRepository extends Repository<RoomEntity, Long> {

    @Query(
            """
            SELECT new pl.smarthotel.pms.reservations.AvailableRoomTypeRow(
                rt.id, rt.code, rt.name, rt.capacity, rt.basePrice, COUNT(r.id))
            FROM RoomEntity r
            JOIN r.roomType rt
            WHERE rt.active = true
              AND rt.capacity >= :guests
              AND r.status = pl.smarthotel.pms.rooms.RoomStatus.AVAILABLE
              AND NOT EXISTS (
                  SELECT 1 FROM ReservationEntity res
                  WHERE res.room = r
                    AND res.status IN (
                        pl.smarthotel.pms.reservations.ReservationStatus.CONFIRMED,
                        pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_IN)
                    AND res.checkIn < :checkOut
                    AND res.checkOut > :checkIn
              )
            GROUP BY rt.id, rt.code, rt.name, rt.capacity, rt.basePrice
            HAVING COUNT(r.id) > 0
            ORDER BY rt.code
            """)
    List<AvailableRoomTypeRow> findAvailableRoomTypes(
            @Param("checkIn") LocalDate checkIn,
            @Param("checkOut") LocalDate checkOut,
            @Param("guests") int guests);
}
