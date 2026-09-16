package pl.smarthotel.pms.rooms;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
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
@RequestMapping(ApiPaths.ADMIN + "/rooms")
@PreAuthorize("hasRole('ADMIN')")
public class RoomController {

    private final RoomService roomService;

    public RoomController(RoomService roomService) {
        this.roomService = roomService;
    }

    @GetMapping
    PageResponse<RoomResponse> list(
            @RequestParam(required = false) Long roomTypeId,
            @RequestParam(required = false) RoomStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return roomService.list(roomTypeId, status, page, Math.min(size, 100));
    }

    @GetMapping("/{id}")
    RoomResponse get(@PathVariable long id) {
        return roomService.get(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    RoomResponse create(@Valid @RequestBody CreateRoomRequest request) {
        return roomService.create(request);
    }

    @PutMapping("/{id}")
    RoomResponse update(@PathVariable long id, @Valid @RequestBody UpdateRoomRequest request) {
        return roomService.update(id, request);
    }
}
