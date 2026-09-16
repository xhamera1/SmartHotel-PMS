package pl.smarthotel.pms.auth;

import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

/** Builds httpOnly SameSite refresh cookies (ADR-0014). */
@Component
public class RefreshCookieFactory {

    private final RefreshCookieProperties properties;
    private final long refreshTtlSeconds;

    public RefreshCookieFactory(
            RefreshCookieProperties properties,
            @Value("${app.jwt.refresh-token-ttl:86400}") long refreshTtlSeconds) {
        this.properties = properties;
        this.refreshTtlSeconds = refreshTtlSeconds;
    }

    public String cookieName() {
        return properties.name();
    }

    public ResponseCookie create(String refreshToken) {
        return base(refreshToken).maxAge(Duration.ofSeconds(refreshTtlSeconds)).build();
    }

    public ResponseCookie clear() {
        return base("").maxAge(Duration.ZERO).build();
    }

    private ResponseCookie.ResponseCookieBuilder base(String value) {
        return ResponseCookie.from(properties.name(), value)
                .httpOnly(true)
                .secure(properties.secure())
                .sameSite(properties.sameSite())
                .path(properties.path());
    }
}
