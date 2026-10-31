package pl.smarthotel.pms.common.logging;

/**
 * Masks PII before it enters structured logs (Phase 10 — no cleartext emails).
 */
public final class PiiMasker {

    private PiiMasker() {}

    /**
     * Masks an email as {@code a***@domain} (local part reduced to first char + stars). Blank
     * input returns {@code null}.
     */
    public static String maskEmail(String email) {
        if (email == null) {
            return null;
        }
        String trimmed = email.trim();
        if (trimmed.isEmpty()) {
            return null;
        }
        int at = trimmed.indexOf('@');
        if (at <= 0 || at == trimmed.length() - 1) {
            return "***";
        }
        char first = trimmed.charAt(0);
        String domain = trimmed.substring(at);
        return first + "***" + domain;
    }
}
