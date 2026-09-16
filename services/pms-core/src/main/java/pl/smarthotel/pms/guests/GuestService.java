package pl.smarthotel.pms.guests;

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
public class GuestService {

    private final GuestRepository guestRepository;
    private final GuestMapper guestMapper;

    public GuestService(GuestRepository guestRepository, GuestMapper guestMapper) {
        this.guestRepository = guestRepository;
        this.guestMapper = guestMapper;
    }

    public PageResponse<GuestResponse> list(String query, int page, int size) {
        String normalized = StringUtils.hasText(query) ? query.trim() : null;
        Page<GuestEntity> result = guestRepository.search(
                normalized, PageRequest.of(page, size, Sort.by("lastName", "firstName").ascending()));
        return PageResponse.from(result.map(guestMapper::toResponse));
    }

    public GuestResponse get(long id) {
        return guestMapper.toResponse(require(id));
    }

    @Transactional
    public GuestResponse create(CreateGuestRequest request) {
        String email = normalizeEmail(request.email());
        if (guestRepository.existsByEmailIgnoreCase(email)) {
            throw ApplicationException.conflict("Guest email already exists: " + email);
        }
        GuestEntity entity = guestMapper.toEntity(request);
        entity.setEmail(email);
        entity.setFirstName(request.firstName().trim());
        entity.setLastName(request.lastName().trim());
        entity.setPhone(normalizePhone(request.phone()));
        return guestMapper.toResponse(guestRepository.save(entity));
    }

    @Transactional
    public GuestResponse update(long id, UpdateGuestRequest request) {
        GuestEntity entity = require(id);
        String email = normalizeEmail(request.email());
        if (guestRepository.existsByEmailIgnoreCaseAndIdNot(email, id)) {
            throw ApplicationException.conflict("Guest email already exists: " + email);
        }
        guestMapper.updateEntity(request, entity);
        entity.setEmail(email);
        entity.setFirstName(request.firstName().trim());
        entity.setLastName(request.lastName().trim());
        entity.setPhone(normalizePhone(request.phone()));
        return guestMapper.toResponse(guestRepository.save(entity));
    }

    @Transactional
    public void delete(long id) {
        GuestEntity entity = require(id);
        if (guestRepository.countReservations(id) > 0) {
            throw ApplicationException.conflict(
                    "Cannot delete guest " + entity.getEmail() + ": reservations still reference them");
        }
        guestRepository.delete(entity);
    }

    /**
     * Booking path: reuse an existing guest row for the same email (case-insensitive),
     * refreshing name/phone from the latest checkout form; otherwise insert a new row.
     */
    @Transactional
    public GuestEntity findOrCreate(GuestUpsertRequest request) {
        String email = normalizeEmail(request.email());
        GuestEntity entity = guestRepository
                .findByEmailIgnoreCase(email)
                .orElseGet(GuestEntity::new);
        guestMapper.applyUpsert(request, entity);
        entity.setEmail(email);
        entity.setFirstName(request.firstName().trim());
        entity.setLastName(request.lastName().trim());
        entity.setPhone(normalizePhone(request.phone()));
        return guestRepository.save(entity);
    }

    GuestEntity require(long id) {
        return guestRepository
                .findById(id)
                .orElseThrow(() -> ApplicationException.notFound("Guest not found: " + id));
    }

    private static String normalizeEmail(String email) {
        return email.trim();
    }

    private static String normalizePhone(String phone) {
        return StringUtils.hasText(phone) ? phone.trim() : null;
    }
}
