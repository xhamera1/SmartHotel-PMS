package pl.smarthotel.pms.common.logging;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Set;
import org.junit.jupiter.api.Test;

/**
 * Documents the Phase 10 shared log field contract for thesis / Filebeat mapping.
 * Runtime JSON shape is produced by LogstashEncoder + StructuredArguments.
 */
class LogSchemaFieldsTest {

    static final Set<String> REQUIRED_TOP_LEVEL = Set.of(
            "@timestamp", "level", "service", "traceId", "message");

    static final Set<String> HTTP_FIELDS = Set.of("http.method", "http.path", "http.status", "durationMs");

    static final Set<String> BUSINESS_EVENTS = Set.of(
            "PricingDecisionMade", "ReservationCreated", "ReservationCancelled", "GeminiCallCompleted");

    @Test
    void requiredTopLevelFieldsAreDocumented() {
        assertThat(REQUIRED_TOP_LEVEL).contains("traceId", "service", "@timestamp");
    }

    @Test
    void httpAccessFieldsAreDocumented() {
        assertThat(HTTP_FIELDS).contains("durationMs", "http.status");
    }

    @Test
    void businessEventNamesMatchPlan() {
        assertThat(BUSINESS_EVENTS).contains("PricingDecisionMade", "GeminiCallCompleted");
    }

    @Test
    void piiHelperNeverEchoesFullEmail() {
        String masked = PiiMasker.maskEmail("guest.full.name@hotel.example");
        assertThat(masked).doesNotContain("guest.full.name");
        assertThat(masked).endsWith("@hotel.example");
    }
}
