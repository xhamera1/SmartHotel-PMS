package pl.smarthotel.pms.reservations;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RatePlanRepository extends JpaRepository<RatePlanEntity, Long> {

    List<RatePlanEntity> findByActiveTrueOrderBySortOrderAsc();
}
