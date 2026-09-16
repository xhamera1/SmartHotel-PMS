package pl.smarthotel.pms.reservations;

import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class RatePlanService {

    private final RatePlanRepository ratePlanRepository;

    public RatePlanService(RatePlanRepository ratePlanRepository) {
        this.ratePlanRepository = ratePlanRepository;
    }

    public List<RatePlanResponse> listActive() {
        return ratePlanRepository.findByActiveTrueOrderBySortOrderAsc().stream()
                .map(plan -> new RatePlanResponse(
                        plan.getId(),
                        plan.getCode(),
                        plan.getName(),
                        plan.getDescription(),
                        plan.isRefundable(),
                        plan.isBreakfastIncluded(),
                        plan.getPriceModifier(),
                        plan.isActive(),
                        plan.getSortOrder()))
                .toList();
    }
}
