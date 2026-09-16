package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;

import java.sql.SQLException;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;

class ExclusionConstraintTest {

    @Test
    void shouldDetectExclusionSqlState() {
        SQLException sql = new SQLException("conflict", ExclusionConstraint.SQLSTATE);
        assertThat(ExclusionConstraint.isDoubleBooking(new DataIntegrityViolationException("x", sql)))
                .isTrue();
    }

    @Test
    void shouldDetectConstraintNameInMessage() {
        RuntimeException wrapped = new RuntimeException(
                "ERROR: conflicting key value violates exclusion constraint \""
                        + ExclusionConstraint.NAME
                        + "\"");
        assertThat(ExclusionConstraint.isDoubleBooking(new DataIntegrityViolationException("x", wrapped)))
                .isTrue();
    }

    @Test
    void shouldIgnoreUnrelatedIntegrityViolations() {
        SQLException unique = new SQLException("duplicate key", "23505");
        assertThat(ExclusionConstraint.isDoubleBooking(new DataIntegrityViolationException("x", unique)))
                .isFalse();
    }
}
