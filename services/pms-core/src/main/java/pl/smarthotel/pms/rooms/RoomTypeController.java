package pl.smarthotel.pms.rooms;

import static pl.smarthotel.pms.common.config.OpenApiConfig.BEARER_JWT;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@RequestMapping(ApiPaths.ADMIN + "/room-types")
@PreAuthorize("hasRole('ADMIN')")
@Tag(name = "Admin — Room types")
@SecurityRequirement(name = BEARER_JWT)
public class RoomTypeController {

    private final RoomTypeService roomTypeService;

    public RoomTypeController(RoomTypeService roomTypeService) {
        this.roomTypeService = roomTypeService;
    }

    @GetMapping
    PageResponse<RoomTypeResponse> list(
            @RequestParam(required = false) Boolean active,
            @RequestParam(required = false) String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return roomTypeService.list(active, query, page, Math.min(size, 100));
    }

    @GetMapping("/{id}")
    RoomTypeResponse get(@PathVariable long id) {
        return roomTypeService.get(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    RoomTypeResponse create(@Valid @RequestBody CreateRoomTypeRequest request) {
        return roomTypeService.create(request);
    }

    @PutMapping("/{id}")
    RoomTypeResponse update(
            @PathVariable long id, @Valid @RequestBody UpdateRoomTypeRequest request) {
        return roomTypeService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void delete(@PathVariable long id) {
        roomTypeService.delete(id);
    }
}
