package pl.smarthotel.pms.reservations;

import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;
import pl.smarthotel.pms.common.web.ApiPaths;

@RestController
@RequestMapping(ApiPaths.API_V1 + "/reservations")
@Tag(name = "Reservations")
public class ReservationController {

    private final ReservationService reservationService;

    public ReservationController(ReservationService reservationService) {
        this.reservationService = reservationService;
    }

    @PostMapping
    ResponseEntity<ReservationResponse> create(@Valid @RequestBody CreateReservationRequest request) {
        ReservationResponse created = reservationService.create(request, ReservationSource.WEB);
        URI location = ServletUriComponentsBuilder.fromCurrentContextPath()
                .path(ApiPaths.API_V1 + "/reservations/lookup")
                .queryParam("code", created.confirmationCode())
                .queryParam("email", request.guest().email())
                .build()
                .toUri();
        return ResponseEntity.created(location).body(created);
    }

    @GetMapping("/lookup")
    ReservationResponse lookup(@RequestParam String code, @RequestParam String email) {
        return reservationService.lookup(code, email);
    }

    @PostMapping("/{code}/cancel")
    @ResponseStatus(HttpStatus.OK)
    ReservationResponse cancel(
            @PathVariable String code, @RequestParam String email) {
        return reservationService.cancelByGuest(code, email);
    }
}
