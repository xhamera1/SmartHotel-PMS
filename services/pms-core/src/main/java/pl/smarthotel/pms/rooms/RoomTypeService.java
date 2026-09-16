package pl.smarthotel.pms.rooms;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.web.PageResponse;

@Service
@Transactional(readOnly = true)
public class RoomTypeService {

    private final RoomTypeRepository roomTypeRepository;
    private final RoomTypeMapper roomTypeMapper;

    public RoomTypeService(RoomTypeRepository roomTypeRepository, RoomTypeMapper roomTypeMapper) {
        this.roomTypeRepository = roomTypeRepository;
        this.roomTypeMapper = roomTypeMapper;
    }

    public PageResponse<RoomTypeResponse> list(Boolean active, String query, int page, int size) {
        String normalizedQuery = StringUtils.hasText(query) ? query.trim() : null;
        Page<RoomTypeEntity> result = roomTypeRepository.search(
                active,
                normalizedQuery,
                PageRequest.of(page, size, Sort.by("code").ascending()));
        return PageResponse.from(result.map(roomTypeMapper::toResponse));
    }

    public RoomTypeResponse get(long id) {
        return roomTypeMapper.toResponse(require(id));
    }

    @Transactional
    public RoomTypeResponse create(CreateRoomTypeRequest request) {
        String code = request.code().trim();
        if (roomTypeRepository.existsByCodeIgnoreCase(code)) {
            throw ApplicationException.conflict("Room type code already exists: " + code);
        }
        RoomTypeEntity entity = roomTypeMapper.toEntity(request);
        entity.setCode(code);
        return roomTypeMapper.toResponse(roomTypeRepository.save(entity));
    }

    @Transactional
    public RoomTypeResponse update(long id, UpdateRoomTypeRequest request) {
        RoomTypeEntity entity = require(id);
        String code = request.code().trim();
        if (roomTypeRepository.existsByCodeIgnoreCaseAndIdNot(code, id)) {
            throw ApplicationException.conflict("Room type code already exists: " + code);
        }
        roomTypeMapper.updateEntity(request, entity);
        entity.setCode(code);
        return roomTypeMapper.toResponse(roomTypeRepository.save(entity));
    }

    @Transactional
    public void delete(long id) {
        RoomTypeEntity entity = require(id);
        if (roomTypeRepository.countActiveReservations(id) > 0) {
            throw ApplicationException.conflict(
                    "Cannot delete room type "
                            + entity.getCode()
                            + ": it has active reservations (CONFIRMED or CHECKED_IN)");
        }
        if (roomTypeRepository.countRooms(id) > 0) {
            throw ApplicationException.conflict(
                    "Cannot delete room type "
                            + entity.getCode()
                            + ": rooms are still assigned to it");
        }
        if (roomTypeRepository.countRateCalendarEntries(id) > 0) {
            throw ApplicationException.conflict(
                    "Cannot delete room type "
                            + entity.getCode()
                            + ": rate calendar entries still reference it");
        }
        roomTypeRepository.delete(entity);
    }

    RoomTypeEntity require(long id) {
        return roomTypeRepository
                .findById(id)
                .orElseThrow(() -> ApplicationException.notFound("Room type not found: " + id));
    }
}
