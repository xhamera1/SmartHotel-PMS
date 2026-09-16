package pl.smarthotel.pms.guests;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface GuestRepository extends JpaRepository<GuestEntity, Long> {

    Optional<GuestEntity> findByEmailIgnoreCase(String email);

    boolean existsByEmailIgnoreCase(String email);

    boolean existsByEmailIgnoreCaseAndIdNot(String email, Long id);

    @Query(
            """
            SELECT g FROM GuestEntity g
            WHERE :query IS NULL
               OR LOWER(g.email) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
               OR LOWER(g.firstName) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
               OR LOWER(g.lastName) LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
               OR LOWER(CONCAT(g.firstName, ' ', g.lastName))
                    LIKE LOWER(CONCAT('%', CAST(:query AS string), '%'))
            """)
    Page<GuestEntity> search(@Param("query") String query, Pageable pageable);

    @Query(
            value = "SELECT COUNT(*) FROM pms.reservations WHERE guest_id = :guestId",
            nativeQuery = true)
    long countReservations(@Param("guestId") long guestId);
}
