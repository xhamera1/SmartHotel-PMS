package pl.smarthotel.pms.common.web;

/**
 * HTTP header and MDC key for request correlation (plan Phase 2 conventions).
 */
public final class CorrelationIds {

    public static final String HEADER = "X-Request-ID";
    public static final String MDC_KEY = "requestId";

    private CorrelationIds() {}
}
