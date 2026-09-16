package pl.smarthotel.pms.auth;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.auth.refresh-cookie")
public record RefreshCookieProperties(String name, String path, String sameSite, boolean secure) {

    public RefreshCookieProperties {
        if (name == null || name.isBlank()) {
            name = "pms_refresh";
        }
        if (path == null || path.isBlank()) {
            path = "/api/v1/auth";
        }
        if (sameSite == null || sameSite.isBlank()) {
            sameSite = "Strict";
        }
    }
}
