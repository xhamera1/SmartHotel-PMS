package pl.smarthotel.pms.reservations;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RatePlanRepository extends JpaRepository<RatePlanEntity, Long> {

    List<RatePlanEntity> findByActiveTrueOrderBySortOrderAsc();

    Optional<RatePlanEntity> findByCodeIgnoreCase(String code);
}
