package pl.smarthotel.pms.common.web;

import org.slf4j.MDC;

/**
 * HTTP header and MDC keys for request correlation (Phases 2 + 10).
 *
 * <p>{@link #MDC_KEY} ({@code requestId}) stays in Problem Details; {@link #TRACE_MDC_KEY}
 * ({@code traceId}) is the shared log-schema field across services.
 */
public final class CorrelationIds {

    public static final String HEADER = "X-Request-ID";
    public static final String MDC_KEY = "requestId";
    public static final String TRACE_MDC_KEY = "traceId";

    private CorrelationIds() {}

    public static void put(String id) {
        MDC.put(MDC_KEY, id);
        MDC.put(TRACE_MDC_KEY, id);
    }

    public static void clear() {
        MDC.remove(MDC_KEY);
        MDC.remove(TRACE_MDC_KEY);
    }

    /** Best-effort current correlation id for outbound HTTP (may be null). */
    public static String peek() {
        String trace = MDC.get(TRACE_MDC_KEY);
        if (trace != null && !trace.isBlank()) {
            return trace;
        }
        return MDC.get(MDC_KEY);
    }
}
