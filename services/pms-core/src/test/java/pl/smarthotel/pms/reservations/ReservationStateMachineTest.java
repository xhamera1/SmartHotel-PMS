package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.stream.Stream;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.web.ProblemTypes;

/**
 * Illegal-transition matrix from {@code docs/diagrams/reservation-state-machine.md}.
 */
class ReservationStateMachineTest {

    @ParameterizedTest(name = "{0} + {1} → allowed")
    @MethodSource("allowed")
    void shouldAllowLegalTransitions(ReservationStatus from, ReservationAction action) {
        assertThatCode(() -> ReservationStateMachine.guard(from, action)).doesNotThrowAnyException();
    }

    @ParameterizedTest(name = "{0} + {1} → rejected")
    @MethodSource("illegal")
    void shouldRejectIllegalTransitions(ReservationStatus from, ReservationAction action) {
        assertThatThrownBy(() -> ReservationStateMachine.guard(from, action))
                .isInstanceOf(ApplicationException.ConflictException.class)
                .extracting(ex -> ((ApplicationException) ex).getProblemType())
                .isEqualTo(ProblemTypes.ILLEGAL_STATE_TRANSITION);
    }

    static Stream<Arguments> allowed() {
        return Stream.of(
                Arguments.of(ReservationStatus.CONFIRMED, ReservationAction.CHECK_IN),
                Arguments.of(ReservationStatus.CONFIRMED, ReservationAction.CANCEL_GUEST),
                Arguments.of(ReservationStatus.CONFIRMED, ReservationAction.CANCEL_STAFF),
                Arguments.of(ReservationStatus.CONFIRMED, ReservationAction.MARK_NO_SHOW),
                Arguments.of(ReservationStatus.CHECKED_IN, ReservationAction.CHECK_OUT));
    }

    static Stream<Arguments> illegal() {
        return Stream.of(
                Arguments.of(ReservationStatus.CONFIRMED, ReservationAction.CHECK_OUT),
                Arguments.of(ReservationStatus.CHECKED_IN, ReservationAction.CHECK_IN),
                Arguments.of(ReservationStatus.CHECKED_IN, ReservationAction.CANCEL_GUEST),
                Arguments.of(ReservationStatus.CHECKED_IN, ReservationAction.CANCEL_STAFF),
                Arguments.of(ReservationStatus.CHECKED_IN, ReservationAction.MARK_NO_SHOW),
                Arguments.of(ReservationStatus.CHECKED_OUT, ReservationAction.CHECK_IN),
                Arguments.of(ReservationStatus.CHECKED_OUT, ReservationAction.CHECK_OUT),
                Arguments.of(ReservationStatus.CHECKED_OUT, ReservationAction.CANCEL_GUEST),
                Arguments.of(ReservationStatus.CHECKED_OUT, ReservationAction.CANCEL_STAFF),
                Arguments.of(ReservationStatus.CHECKED_OUT, ReservationAction.MARK_NO_SHOW),
                Arguments.of(ReservationStatus.CANCELLED, ReservationAction.CHECK_IN),
                Arguments.of(ReservationStatus.CANCELLED, ReservationAction.CHECK_OUT),
                Arguments.of(ReservationStatus.CANCELLED, ReservationAction.CANCEL_GUEST),
                Arguments.of(ReservationStatus.CANCELLED, ReservationAction.CANCEL_STAFF),
                Arguments.of(ReservationStatus.CANCELLED, ReservationAction.MARK_NO_SHOW),
                Arguments.of(ReservationStatus.NO_SHOW, ReservationAction.CHECK_IN),
                Arguments.of(ReservationStatus.NO_SHOW, ReservationAction.CHECK_OUT),
                Arguments.of(ReservationStatus.NO_SHOW, ReservationAction.CANCEL_GUEST),
                Arguments.of(ReservationStatus.NO_SHOW, ReservationAction.CANCEL_STAFF),
                Arguments.of(ReservationStatus.NO_SHOW, ReservationAction.MARK_NO_SHOW));
    }
}
