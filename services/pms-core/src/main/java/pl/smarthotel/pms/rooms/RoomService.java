package pl.smarthotel.pms.rooms;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.web.PageResponse;

@Service
@Transactional(readOnly = true)
public class RoomService {

    private final RoomRepository roomRepository;
    private final RoomTypeService roomTypeService;
    private final RoomMapper roomMapper;

    public RoomService(
            RoomRepository roomRepository, RoomTypeService roomTypeService, RoomMapper roomMapper) {
        this.roomRepository = roomRepository;
        this.roomTypeService = roomTypeService;
        this.roomMapper = roomMapper;
    }

    public PageResponse<RoomResponse> list(Long roomTypeId, RoomStatus status, int page, int size) {
        Page<RoomEntity> result = roomRepository.search(
                roomTypeId,
                status,
                PageRequest.of(page, size, Sort.by("roomNumber").ascending()));
        return PageResponse.from(result.map(roomMapper::toResponse));
    }

    public RoomResponse get(long id) {
        return roomMapper.toResponse(requireWithType(id));
    }

    @Transactional
    public RoomResponse create(CreateRoomRequest request) {
        String roomNumber = request.roomNumber().trim();
        if (roomRepository.existsByRoomNumberIgnoreCase(roomNumber)) {
            throw ApplicationException.conflict("Room number already exists: " + roomNumber);
        }
        RoomTypeEntity roomType = roomTypeService.require(request.roomTypeId());
        RoomEntity entity = new RoomEntity();
        entity.setRoomNumber(roomNumber);
        entity.setRoomType(roomType);
        entity.setFloor(request.floor());
        entity.setStatus(request.status() == null ? RoomStatus.AVAILABLE : request.status());
        entity.setNotes(request.notes());
        return roomMapper.toResponse(roomRepository.save(entity));
    }

    @Transactional
    public RoomResponse update(long id, UpdateRoomRequest request) {
        RoomEntity entity = requireWithType(id);
        String roomNumber = request.roomNumber().trim();
        if (roomRepository.existsByRoomNumberIgnoreCaseAndIdNot(roomNumber, id)) {
            throw ApplicationException.conflict("Room number already exists: " + roomNumber);
        }
        if (entity.getStatus() != request.status()
                && request.status() == RoomStatus.OUT_OF_SERVICE
                && roomRepository.countActiveReservations(id) > 0) {
            throw ApplicationException.conflict(
                    "Cannot mark room "
                            + entity.getRoomNumber()
                            + " OUT_OF_SERVICE while it has active reservations");
        }
        RoomTypeEntity roomType = roomTypeService.require(request.roomTypeId());
        entity.setRoomNumber(roomNumber);
        entity.setRoomType(roomType);
        entity.setFloor(request.floor());
        entity.setStatus(request.status());
        entity.setNotes(request.notes());
        return roomMapper.toResponse(roomRepository.save(entity));
    }

    private RoomEntity requireWithType(long id) {
        return roomRepository
                .findByIdWithType(id)
                .orElseThrow(() -> ApplicationException.notFound("Room not found: " + id));
    }
}
