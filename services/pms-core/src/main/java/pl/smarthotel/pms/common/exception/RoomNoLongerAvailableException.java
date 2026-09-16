package pl.smarthotel.pms.common.exception;

import java.time.LocalDate;
import org.springframework.http.HttpStatus;
import pl.smarthotel.pms.common.web.ProblemTypes;

/**
 * Raised when inventory looked free but the booking lost the race — including when PostgreSQL
 * rejects the insert via the {@code no_double_booking} exclusion constraint.
 */
public final class RoomNoLongerAvailableException extends ApplicationException {

    public RoomNoLongerAvailableException(String detail) {
        super(
                ProblemTypes.ROOM_NO_LONGER_AVAILABLE,
                HttpStatus.CONFLICT,
                "Room no longer available",
                detail);
    }

    public static RoomNoLongerAvailableException forStay(
            String roomTypeCode, LocalDate checkIn, LocalDate checkOut) {
        return new RoomNoLongerAvailableException(
                "No " + roomTypeCode + " room is free for " + checkIn + " – " + checkOut + " anymore.");
    }
}
