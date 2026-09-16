package pl.smarthotel.pms.rooms;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface RoomTypeRepository extends JpaRepository<RoomTypeEntity, Long> {

    boolean existsByCodeIgnoreCase(String code);

    boolean existsByCodeIgnoreCaseAndIdNot(String code, Long id);

    @Query(
            """
            SELECT rt FROM RoomTypeEntity rt
            WHERE (:active IS NULL OR rt.active = :active)
              AND (:query IS NULL OR LOWER(rt.code) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
                   OR LOWER(rt.name) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%')))
            """)
    Page<RoomTypeEntity> search(
            @Param("active") Boolean active, @Param("query") String query, Pageable pageable);

    @Query(
            value =
                    """
                    SELECT COUNT(*)
                    FROM pms.reservations res
                    INNER JOIN pms.rooms room ON room.id = res.room_id
                    WHERE room.room_type_id = :roomTypeId
                      AND res.status IN ('CONFIRMED', 'CHECKED_IN')
                    """,
            nativeQuery = true)
    long countActiveReservations(@Param("roomTypeId") long roomTypeId);

    @Query(value = "SELECT COUNT(*) FROM pms.rooms WHERE room_type_id = :roomTypeId", nativeQuery = true)
    long countRooms(@Param("roomTypeId") long roomTypeId);

    @Query(
            value = "SELECT COUNT(*) FROM pms.rate_calendar WHERE room_type_id = :roomTypeId",
            nativeQuery = true)
    long countRateCalendarEntries(@Param("roomTypeId") long roomTypeId);

    Optional<RoomTypeEntity> findByCodeIgnoreCase(String code);
}
