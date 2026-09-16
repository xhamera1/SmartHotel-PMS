package pl.smarthotel.pms.reservations;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;
import pl.smarthotel.pms.common.web.ApiPaths;

@RestController
@RequestMapping(ApiPaths.ADMIN + "/reservations")
@PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
@Tag(name = "Admin — Reservations")
@SecurityRequirement(name = BEARER_JWT)
public class AdminReservationController {

    private final ReservationService reservationService;

    public AdminReservationController(ReservationService reservationService) {
        this.reservationService = reservationService;
    }

    @PostMapping
    ResponseEntity<ReservationResponse> create(@Valid @RequestBody CreateReservationRequest request) {
        ReservationResponse created = reservationService.create(request, ReservationSource.ADMIN);
        URI location = ServletUriComponentsBuilder.fromCurrentContextPath()
                .path(ApiPaths.ADMIN + "/reservations/{id}")
                .buildAndExpand(created.id())
                .toUri();
        return ResponseEntity.created(location).body(created);
    }

    @PostMapping("/{id}/check-in")
    ReservationResponse checkIn(@PathVariable long id) {
        return reservationService.checkIn(id);
    }

    @PostMapping("/{id}/check-out")
    ReservationResponse checkOut(@PathVariable long id) {
        return reservationService.checkOut(id);
    }

    @PostMapping("/{id}/cancel")
    ReservationResponse cancel(@PathVariable long id) {
        return reservationService.cancelByStaff(id);
    }
}
