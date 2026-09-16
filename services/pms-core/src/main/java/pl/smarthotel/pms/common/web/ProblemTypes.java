package pl.smarthotel.pms.common.web;

/**
 * RFC 7807 {@code type} URIs for {@code application/problem+json} responses.
 *
 * <p>Stable contract — clients and the frontend branch on these strings. Keep in sync with the
 * catalog table in {@code docs/api/pms-api.md}.
 */
public final class ProblemTypes {

    public static final String BASE = "https://smarthotel/problems";

    /** Bean Validation / malformed request / bad query params. HTTP 400 (or 405 for wrong method). */
    public static final String VALIDATION_ERROR = BASE + "/validation-error";

    /** Resource missing. HTTP 404. */
    public static final String NOT_FOUND = BASE + "/not-found";

    /** Generic business conflict (duplicate email/code, etc.). HTTP 409. */
    public static final String CONFLICT = BASE + "/conflict";

    /** Missing/invalid credentials or JWT. HTTP 401. */
    public static final String UNAUTHORIZED = BASE + "/unauthorized";

    /** Authenticated but role insufficient. HTTP 403. */
    public static final String FORBIDDEN = BASE + "/forbidden";

    /** Login rate limit exceeded. HTTP 429. */
    public static final String RATE_LIMITED = BASE + "/rate-limited";

    /** Concurrent booking lost the race / inventory gone. HTTP 409. */
    public static final String ROOM_NO_LONGER_AVAILABLE = BASE + "/room-no-longer-available";

    /** Guest cancel blocked by non-refundable rate plan. HTTP 409. */
    public static final String RATE_PLAN_NOT_REFUNDABLE = BASE + "/rate-plan-not-refundable";

    /** Reservation state machine rejection. HTTP 409. */
    public static final String ILLEGAL_STATE_TRANSITION = BASE + "/illegal-state-transition";

    /** Unexpected failure. HTTP 500. */
    public static final String INTERNAL_ERROR = BASE + "/internal-error";

    private ProblemTypes() {}
}
