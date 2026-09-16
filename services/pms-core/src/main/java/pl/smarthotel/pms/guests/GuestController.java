package pl.smarthotel.pms.guests;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.web.ApiPaths;
import pl.smarthotel.pms.common.web.PageResponse;

@RestController
@RequestMapping(ApiPaths.ADMIN + "/guests")
@PreAuthorize("hasAnyRole('ADMIN', 'RECEPTIONIST')")
public class GuestController {

    private final GuestService guestService;

    public GuestController(GuestService guestService) {
        this.guestService = guestService;
    }

    @GetMapping
    PageResponse<GuestResponse> list(
            @RequestParam(required = false) String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return guestService.list(query, page, Math.min(size, 100));
    }

    @GetMapping("/{id}")
    GuestResponse get(@PathVariable long id) {
        return guestService.get(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    GuestResponse create(@Valid @RequestBody CreateGuestRequest request) {
        return guestService.create(request);
    }

    @PutMapping("/{id}")
    GuestResponse update(@PathVariable long id, @Valid @RequestBody UpdateGuestRequest request) {
        return guestService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void delete(@PathVariable long id) {
        guestService.delete(id);
    }
}
