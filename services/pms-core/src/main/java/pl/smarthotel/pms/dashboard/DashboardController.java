package pl.smarthotel.pms.dashboard;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.web.ApiPaths;

@RestController
@RequestMapping(ApiPaths.ADMIN + "/dashboard")
@PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
@Tag(name = "Admin — Dashboard")
@SecurityRequirement(name = BEARER_JWT)
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/kpis")
    DashboardKpisResponse kpis() {
        return dashboardService.kpis();
    }

    @GetMapping("/timeseries")
    DashboardTimeseriesResponse timeseries(@RequestParam(defaultValue = "30") int days) {
        return dashboardService.timeseries(days);
    }
}
