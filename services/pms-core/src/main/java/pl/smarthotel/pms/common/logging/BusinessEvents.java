package pl.smarthotel.pms.common.logging;

import static net.logstash.logback.argument.StructuredArguments.kv;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Structured business / thesis telemetry events (Phase 10). Fields land as JSON via LogstashEncoder.
 */
public final class BusinessEvents {

    private static final Logger log = LoggerFactory.getLogger("pl.smarthotel.business");

    private BusinessEvents() {}

    public static void reservationCreated(
            String confirmationCode, String roomTypeCode, String source) {
        log.info(
                "ReservationCreated",
                kv("businessEvent", "ReservationCreated"),
                kv("confirmationCode", confirmationCode),
                kv("roomType", roomTypeCode),
                kv("source", source));
    }

    public static void reservationCancelled(String confirmationCode, String actor) {
        log.info(
                "ReservationCancelled",
                kv("businessEvent", "ReservationCancelled"),
                kv("confirmationCode", confirmationCode),
                kv("actor", actor));
    }

    public static void pricingDecisionMade(
            String date,
            String roomType,
            String price,
            String multiplier,
            String source,
            String modelVersion,
            Integer demandIndicator) {
        log.info(
                "PricingDecisionMade",
                kv("businessEvent", "PricingDecisionMade"),
                kv("date", date),
                kv("roomType", roomType),
                kv("price", price),
                kv("multiplier", multiplier),
                kv("source", source),
                kv("modelVersion", modelVersion),
                kv("demandIndicator", demandIndicator));
    }
}
