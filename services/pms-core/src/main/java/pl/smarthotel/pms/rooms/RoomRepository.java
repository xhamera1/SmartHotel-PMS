package pl.smarthotel.pms.rooms;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface RoomRepository extends JpaRepository<RoomEntity, Long> {

    boolean existsByRoomNumberIgnoreCase(String roomNumber);

    boolean existsByRoomNumberIgnoreCaseAndIdNot(String roomNumber, Long id);

    @EntityGraph(attributePaths = "roomType")
    @Query(
            """
            SELECT r FROM RoomEntity r
            WHERE (:roomTypeId IS NULL OR r.roomType.id = :roomTypeId)
              AND (:status IS NULL OR r.status = :status)
            """)
    Page<RoomEntity> search(
            @Param("roomTypeId") Long roomTypeId,
            @Param("status") RoomStatus status,
            Pageable pageable);

    @EntityGraph(attributePaths = "roomType")
    @Query("SELECT r FROM RoomEntity r WHERE r.id = :id")
    Optional<RoomEntity> findByIdWithType(@Param("id") Long id);

    @Query(
            value =
                    """
                    SELECT COUNT(*) FROM pms.reservations res
                    WHERE res.room_id = :roomId
                      AND res.status IN ('CONFIRMED', 'CHECKED_IN')
                    """,
            nativeQuery = true)
    long countActiveReservations(@Param("roomId") long roomId);

    long countByStatusNot(RoomStatus status);
}
