package pl.smarthotel.pms.common.web;

/**
 * RFC 7807 {@code type} URIs for problem+json responses. Keep stable — clients and
 * the frontend branch on these strings.
 */
public final class ProblemTypes {

    public static final String BASE = "https://smarthotel/problems";

    public static final String VALIDATION_ERROR = BASE + "/validation-error";
    public static final String NOT_FOUND = BASE + "/not-found";
    public static final String CONFLICT = BASE + "/conflict";
    public static final String ROOM_NO_LONGER_AVAILABLE = BASE + "/room-no-longer-available";
    public static final String RATE_PLAN_NOT_REFUNDABLE = BASE + "/rate-plan-not-refundable";
    public static final String ILLEGAL_STATE_TRANSITION = BASE + "/illegal-state-transition";
    public static final String INTERNAL_ERROR = BASE + "/internal-error";

    private ProblemTypes() {}
}
