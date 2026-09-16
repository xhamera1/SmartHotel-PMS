package pl.smarthotel.pms.reservations;

import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.web.ProblemTypes;

/**
 * Status × action matrix from {@code docs/diagrams/reservation-state-machine.md}.
 * Business-date guards (check-in window, guest cancel cut-off) live in the service.
 */
public final class ReservationStateMachine {

    private ReservationStateMachine() {}

    public static void guard(ReservationStatus status, ReservationAction action) {
        if (!allowed(status, action)) {
            throw new ApplicationException.ConflictException(
                    ProblemTypes.ILLEGAL_STATE_TRANSITION,
                    "Illegal state transition",
                    "Cannot " + action.name().toLowerCase().replace('_', '-')
                            + " a reservation in status " + status);
        }
    }

    static boolean allowed(ReservationStatus status, ReservationAction action) {
        return switch (status) {
            case CONFIRMED -> action == ReservationAction.CHECK_IN
                    || action == ReservationAction.CANCEL_GUEST
                    || action == ReservationAction.CANCEL_STAFF
                    || action == ReservationAction.MARK_NO_SHOW;
            case CHECKED_IN -> action == ReservationAction.CHECK_OUT;
            case CHECKED_OUT, CANCELLED, NO_SHOW -> false;
        };
    }
}
