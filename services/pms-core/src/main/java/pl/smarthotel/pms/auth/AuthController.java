package pl.smarthotel.pms.auth;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.exception.ApplicationException;
import pl.smarthotel.pms.common.web.ApiPaths;

@RestController
@RequestMapping(ApiPaths.API_V1 + "/auth")
@Tag(name = "Auth")
public class AuthController {

    private final AuthService authService;
    private final LoginRateLimiter loginRateLimiter;
    private final RefreshCookieFactory refreshCookieFactory;

    public AuthController(
            AuthService authService,
            LoginRateLimiter loginRateLimiter,
            RefreshCookieFactory refreshCookieFactory) {
        this.authService = authService;
        this.loginRateLimiter = loginRateLimiter;
        this.refreshCookieFactory = refreshCookieFactory;
    }

    @PostMapping("/login")
    @Operation(
            summary = "Staff login",
            description =
                    "Returns an access JWT in the body and sets the refresh JWT as an "
                            + "httpOnly; SameSite=Strict cookie (ADR-0014).")
    ResponseEntity<TokenResponse> login(
            @Valid @RequestBody LoginRequest request, HttpServletRequest http) {
        loginRateLimiter.check(clientKey(http));
        AuthService.SessionTokens session = authService.login(request);
        return withRefreshCookie(session);
    }

    @PostMapping("/refresh")
    @Operation(
            summary = "Silent refresh",
            description =
                    "Reads the httpOnly refresh cookie (default name pms_refresh), rotates "
                            + "tokens, and returns a new access JWT. No request body.")
    ResponseEntity<TokenResponse> refresh(HttpServletRequest request) {
        String refreshToken = readCookie(request, refreshCookieFactory.cookieName());
        if (refreshToken == null || refreshToken.isBlank()) {
            throw ApplicationException.unauthorized("Missing refresh token");
        }
        AuthService.SessionTokens session = authService.refresh(refreshToken);
        return withRefreshCookie(session);
    }

    @PostMapping("/logout")
    @Operation(summary = "Staff logout", description = "Clears the refresh cookie.")
    ResponseEntity<Void> logout() {
        return ResponseEntity.noContent()
                .header(HttpHeaders.SET_COOKIE, refreshCookieFactory.clear().toString())
                .build();
    }

    private ResponseEntity<TokenResponse> withRefreshCookie(AuthService.SessionTokens session) {
        return ResponseEntity.ok()
                .header(
                        HttpHeaders.SET_COOKIE,
                        refreshCookieFactory.create(session.refreshToken()).toString())
                .body(session.access());
    }

    private static String readCookie(HttpServletRequest request, String name) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return null;
        }
        for (Cookie cookie : cookies) {
            if (name.equals(cookie.getName())) {
                return cookie.getValue();
            }
        }
        return null;
    }

    private static String clientKey(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isBlank()) {
            return forwarded.split(",")[0].trim();
        }
        return request.getRemoteAddr() != null ? request.getRemoteAddr() : "unknown";
    }
}
