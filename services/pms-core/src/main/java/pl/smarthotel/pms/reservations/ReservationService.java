package pl.smarthotel.pms.reservations;

import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.config.ClockConfig;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.exception.RoomNoLongerAvailableException;
import pl.smarthotel.pms.common.web.ProblemTypes;
import pl.smarthotel.pms.guests.GuestEntity;
import pl.smarthotel.pms.guests.GuestService;
import pl.smarthotel.pms.ratecalendar.NightlyBar;
import pl.smarthotel.pms.ratecalendar.PriceProvider;
import pl.smarthotel.pms.rooms.RoomEntity;
import pl.smarthotel.pms.rooms.RoomTypeEntity;
import pl.smarthotel.pms.rooms.RoomTypeRepository;

@Service
@Transactional(readOnly = true)
public class ReservationService {

    private static final Logger log = LoggerFactory.getLogger(ReservationService.class);
    private static final String CURRENCY = "PLN";

    private final ReservationRepository reservationRepository;
    private final RatePlanRepository ratePlanRepository;
    private final RoomTypeRepository roomTypeRepository;
    private final GuestService guestService;
    private final PriceProvider priceProvider;
    private final ConfirmationCodeGenerator confirmationCodeGenerator;
    private final Clock clock;
    private final ZoneId hotelZone;

    public ReservationService(
            ReservationRepository reservationRepository,
            RatePlanRepository ratePlanRepository,
            RoomTypeRepository roomTypeRepository,
            GuestService guestService,
            PriceProvider priceProvider,
            ConfirmationCodeGenerator confirmationCodeGenerator,
            Clock clock,
            @Qualifier(ClockConfig.HOTEL_ZONE_BEAN) ZoneId hotelZone) {
        this.reservationRepository = reservationRepository;
        this.ratePlanRepository = ratePlanRepository;
        this.roomTypeRepository = roomTypeRepository;
        this.guestService = guestService;
        this.priceProvider = priceProvider;
        this.confirmationCodeGenerator = confirmationCodeGenerator;
        this.clock = clock;
        this.hotelZone = hotelZone;
    }

    @Transactional
    public ReservationResponse create(CreateReservationRequest request, ReservationSource source) {
        RoomTypeEntity roomType = roomTypeRepository
                .findByCodeIgnoreCase(request.roomTypeCode().trim())
                .orElseThrow(() -> ApplicationException.notFound(
                        "Room type not found: " + request.roomTypeCode()));
        if (!roomType.isActive()) {
            throw ApplicationException.badRequest("Room type is not active: " + roomType.getCode());
        }
        if (request.adults() > roomType.getCapacity()) {
            throw ApplicationException.badRequest(
                    "Party size " + request.adults() + " exceeds capacity " + roomType.getCapacity()
                            + " for " + roomType.getCode());
        }

        RatePlanEntity ratePlan = ratePlanRepository
                .findByCodeIgnoreCase(request.ratePlanCode().trim())
                .orElseThrow(() -> ApplicationException.notFound(
                        "Rate plan not found: " + request.ratePlanCode()));
        if (!ratePlan.isActive()) {
            throw ApplicationException.badRequest("Rate plan is not active: " + ratePlan.getCode());
        }

        List<RoomEntity> free = reservationRepository.findFreeRooms(
                roomType.getId(), request.checkIn(), request.checkOut(), PageRequest.of(0, 1));
        if (free.isEmpty()) {
            throw RoomNoLongerAvailableException.forStay(
                    roomType.getCode(), request.checkIn(), request.checkOut());
        }
        RoomEntity room = free.getFirst();

        GuestEntity guest = guestService.findOrCreate(request.guest());

        List<NightlyBar> bars = priceProvider.resolveBars(
                roomType.getId(), roomType.getBasePrice(), request.checkIn(), request.checkOut());
        List<PriceBreakdownLine> breakdown =
                ReservationPricing.snapshot(bars, ratePlan.getPriceModifier());

        ReservationEntity entity = new ReservationEntity();
        entity.setConfirmationCode(confirmationCodeGenerator.next());
        entity.setGuest(guest);
        entity.setRoom(room);
        entity.setRatePlan(ratePlan);
        entity.setCheckIn(request.checkIn());
        entity.setCheckOut(request.checkOut());
        entity.setStatus(ReservationStatus.CONFIRMED);
        entity.setAdults(request.adults());
        entity.setPriceBreakdown(breakdown);
        entity.setTotalPrice(ReservationPricing.total(breakdown));
        entity.setCurrency(CURRENCY);
        entity.setSource(source);

        try {
            return toResponse(reservationRepository.saveAndFlush(entity));
        } catch (DataIntegrityViolationException ex) {
            if (ExclusionConstraint.isDoubleBooking(ex)) {
                throw RoomNoLongerAvailableException.forStay(
                        roomType.getCode(), request.checkIn(), request.checkOut());
            }
            throw ex;
        }
    }

    public ReservationResponse lookup(String code, String email) {
        return toResponse(requireByCodeAndEmail(code, email));
    }

    @Transactional
    public ReservationResponse cancelByGuest(String code, String email) {
        ReservationEntity reservation = requireByCodeAndEmail(code, email);
        ReservationStateMachine.guard(reservation.getStatus(), ReservationAction.CANCEL_GUEST);

        LocalDate today = businessDate();
        if (!today.isBefore(reservation.getCheckIn())) {
            throw new ApplicationException.ConflictException(
                    ProblemTypes.ILLEGAL_STATE_TRANSITION,
                    "Illegal state transition",
                    "Guest cancellation is only allowed before the check-in date");
        }
        if (!reservation.getRatePlan().isRefundable()) {
            throw new ApplicationException.ConflictException(
                    ProblemTypes.RATE_PLAN_NOT_REFUNDABLE,
                    "Rate plan is not refundable",
                    "Reservation " + reservation.getConfirmationCode() + " uses the "
                            + reservation.getRatePlan().getCode()
                            + " rate and cannot be cancelled online.");
        }

        reservation.setStatus(ReservationStatus.CANCELLED);
        return toResponse(reservationRepository.save(reservation));
    }

    @Transactional
    public ReservationResponse checkIn(long id) {
        ReservationEntity reservation = requireById(id);
        ReservationStateMachine.guard(reservation.getStatus(), ReservationAction.CHECK_IN);

        LocalDate today = businessDate();
        if (today.isBefore(reservation.getCheckIn()) || !today.isBefore(reservation.getCheckOut())) {
            throw new ApplicationException.ConflictException(
                    ProblemTypes.ILLEGAL_STATE_TRANSITION,
                    "Illegal state transition",
                    "Check-in is only allowed on business dates from check-in inclusive to check-out exclusive");
        }

        reservation.setStatus(ReservationStatus.CHECKED_IN);
        return toResponse(reservationRepository.save(reservation));
    }

    @Transactional
    public ReservationResponse checkOut(long id) {
        ReservationEntity reservation = requireById(id);
        ReservationStateMachine.guard(reservation.getStatus(), ReservationAction.CHECK_OUT);
        reservation.setStatus(ReservationStatus.CHECKED_OUT);
        return toResponse(reservationRepository.save(reservation));
    }

    @Transactional
    public ReservationResponse cancelByStaff(long id) {
        ReservationEntity reservation = requireById(id);
        ReservationStateMachine.guard(reservation.getStatus(), ReservationAction.CANCEL_STAFF);
        reservation.setStatus(ReservationStatus.CANCELLED);
        return toResponse(reservationRepository.save(reservation));
    }

    /**
     * Night audit (T5): mark still-{@code CONFIRMED} stays whose check-in date is strictly
     * before the hotel business date as {@code NO_SHOW}. Idempotent.
     */
    @Transactional
    public int markNoShows() {
        return markNoShows(businessDate());
    }

    /** Testable entry point — production job uses {@link #markNoShows()}. */
    @Transactional
    public int markNoShows(LocalDate businessDate) {
        List<ReservationEntity> stale = reservationRepository.findConfirmedWithCheckInBefore(businessDate);
        for (ReservationEntity reservation : stale) {
            ReservationStateMachine.guard(reservation.getStatus(), ReservationAction.MARK_NO_SHOW);
            reservation.setStatus(ReservationStatus.NO_SHOW);
            reservationRepository.save(reservation);
            log.warn(
                    "Night audit marked reservation {} as NO_SHOW (check-in {}, business date {})",
                    reservation.getConfirmationCode(),
                    reservation.getCheckIn(),
                    businessDate);
        }
        return stale.size();
    }

    LocalDate businessDate() {
        return LocalDate.ofInstant(clock.instant(), hotelZone);
    }

    private ReservationEntity requireByCodeAndEmail(String code, String email) {
        return reservationRepository
                .findByConfirmationCodeAndGuestEmailIgnoreCase(code.trim(), email.trim())
                .orElseThrow(() -> ApplicationException.notFound(
                        "Reservation not found for code " + code + " and email"));
    }

    private ReservationEntity requireById(long id) {
        return reservationRepository
                .findByIdForUpdate(id)
                .orElseThrow(() -> ApplicationException.notFound("Reservation not found: " + id));
    }

    static ReservationResponse toResponse(ReservationEntity entity) {
        RatePlanEntity plan = entity.getRatePlan();
        return new ReservationResponse(
                entity.getId(),
                entity.getConfirmationCode(),
                entity.getStatus(),
                entity.getRoom().getRoomType().getCode(),
                entity.getRoom().getRoomNumber(),
                new ReservationResponse.RatePlanSummary(
                        plan.getCode(), plan.isRefundable(), plan.isBreakfastIncluded()),
                entity.getCheckIn(),
                entity.getCheckOut(),
                entity.getAdults(),
                entity.getTotalPrice(),
                entity.getCurrency(),
                entity.getPriceBreakdown(),
                entity.getSource());
    }
}
