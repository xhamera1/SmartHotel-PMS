package pl.smarthotel.pms.reservations;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import pl.smarthotel.pms.rooms.RoomEntity;

public interface ReservationRepository extends JpaRepository<ReservationEntity, Long> {

    boolean existsByConfirmationCode(String confirmationCode);

    @EntityGraph(attributePaths = {"guest", "room", "room.roomType", "ratePlan"})
    @Query(
            """
            SELECT r FROM ReservationEntity r
            JOIN r.guest g
            WHERE r.confirmationCode = :code
              AND LOWER(g.email) = LOWER(:email)
            """)
    Optional<ReservationEntity> findByConfirmationCodeAndGuestEmailIgnoreCase(
            @Param("code") String code, @Param("email") String email);

    @EntityGraph(attributePaths = {"guest", "room", "room.roomType", "ratePlan"})
    @Query("SELECT r FROM ReservationEntity r WHERE r.id = :id")
    Optional<ReservationEntity> findByIdForUpdate(@Param("id") long id);

    @Query(
            """
            SELECT r FROM RoomEntity r
            JOIN r.roomType rt
            WHERE rt.id = :roomTypeId
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
            ORDER BY r.roomNumber
            """)
    List<RoomEntity> findFreeRooms(
            @Param("roomTypeId") Long roomTypeId,
            @Param("checkIn") LocalDate checkIn,
            @Param("checkOut") LocalDate checkOut,
            Pageable pageable);

    @EntityGraph(attributePaths = {"guest", "room", "room.roomType", "ratePlan"})
    @Query(
            """
            SELECT r FROM ReservationEntity r
            WHERE r.status = pl.smarthotel.pms.reservations.ReservationStatus.CONFIRMED
              AND r.checkIn < :businessDate
            """)
    List<ReservationEntity> findConfirmedWithCheckInBefore(@Param("businessDate") LocalDate businessDate);

    @EntityGraph(attributePaths = {"guest", "room", "room.roomType", "ratePlan"})
    @Query(
            """
            SELECT r FROM ReservationEntity r
            JOIN r.guest g
            WHERE (:status IS NULL OR r.status = :status)
              AND (:from IS NULL OR r.checkIn >= :from)
              AND (:to IS NULL OR r.checkIn < :to)
              AND (
                    :query IS NULL
                    OR LOWER(r.confirmationCode) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
                    OR LOWER(g.email) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
                    OR LOWER(g.firstName) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
                    OR LOWER(g.lastName) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
                    OR LOWER(CONCAT(g.firstName, ' ', g.lastName))
                        LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
                  )
            """)
    Page<ReservationEntity> searchAdmin(
            @Param("status") ReservationStatus status,
            @Param("from") LocalDate from,
            @Param("to") LocalDate to,
            @Param("query") String query,
            Pageable pageable);

    @Query(
            """
            SELECT COUNT(DISTINCT r.room.id) FROM ReservationEntity r
            WHERE r.status IN (
                    pl.smarthotel.pms.reservations.ReservationStatus.CONFIRMED,
                    pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_IN)
              AND r.checkIn <= :day
              AND r.checkOut > :day
            """)
    long countOccupiedRoomsOn(@Param("day") LocalDate day);

    @Query(
            """
            SELECT COUNT(r) FROM ReservationEntity r
            WHERE r.status IN (
                    pl.smarthotel.pms.reservations.ReservationStatus.CONFIRMED,
                    pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_IN)
              AND r.checkIn = :day
            """)
    long countArrivalsOn(@Param("day") LocalDate day);

    @Query(
            """
            SELECT COUNT(r) FROM ReservationEntity r
            WHERE r.status IN (
                    pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_IN,
                    pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_OUT)
              AND r.checkOut = :day
            """)
    long countDeparturesOn(@Param("day") LocalDate day);

    @Query(
            """
            SELECT COALESCE(SUM(r.totalPrice), 0) FROM ReservationEntity r
            WHERE r.status IN (
                    pl.smarthotel.pms.reservations.ReservationStatus.CONFIRMED,
                    pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_IN,
                    pl.smarthotel.pms.reservations.ReservationStatus.CHECKED_OUT)
              AND r.checkIn >= :monthStart
              AND r.checkIn < :monthEnd
            """)
    BigDecimal sumMtdRevenue(
            @Param("monthStart") LocalDate monthStart, @Param("monthEnd") LocalDate monthEnd);
}
