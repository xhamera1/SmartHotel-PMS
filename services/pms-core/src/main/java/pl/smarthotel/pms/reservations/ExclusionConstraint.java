package pl.smarthotel.pms.reservations;

import java.sql.SQLException;

/**
 * Detects PostgreSQL exclusion-constraint failures for {@code no_double_booking}
 * (SQLSTATE {@code 23P01}). Avoids a compile-time dependency on the PG driver
 * (runtime scope) by inspecting {@link SQLException#getSQLState()} and messages.
 */
final class ExclusionConstraint {

    static final String NAME = "no_double_booking";
    static final String SQLSTATE = "23P01";

    private ExclusionConstraint() {}

    static boolean isDoubleBooking(Throwable throwable) {
        for (Throwable t = throwable; t != null; t = t.getCause()) {
            if (t instanceof SQLException sql && SQLSTATE.equals(sql.getSQLState())) {
                return true;
            }
            String message = t.getMessage();
            if (message != null && message.contains(NAME)) {
                return true;
            }
        }
        return false;
    }
}
