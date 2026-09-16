package pl.smarthotel.pms.reservations;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.web.ApiPaths;

@RestController
@RequestMapping(ApiPaths.ADMIN + "/rate-plans")
@PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
@Tag(name = "Admin — Rate plans")
@SecurityRequirement(name = BEARER_JWT)
public class RatePlanController {

    private final RatePlanService ratePlanService;

    public RatePlanController(RatePlanService ratePlanService) {
        this.ratePlanService = ratePlanService;
    }

    @GetMapping
    List<RatePlanResponse> list() {
        return ratePlanService.listActive();
    }
}
