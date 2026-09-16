package pl.smarthotel.pms.auth;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

/** Shared helpers for integration tests that need a staff JWT. */
public final class AuthTestSupport {

    public static final String ADMIN_EMAIL = "admin@smarthotel.local";
    public static final String ADMIN_PASSWORD = "admin-dev-password";
    public static final String RECEPTION_EMAIL = "reception@smarthotel.local";
    public static final String RECEPTION_PASSWORD = "reception-dev-password";
    public static final String REFRESH_COOKIE = "pms_refresh";

    private AuthTestSupport() {}

    public static String loginAccessToken(TestRestTemplate rest, String email, String password) {
        ResponseEntity<TokenResponse> response = rest.postForEntity(
                "/api/v1/auth/login",
                Map.of("email", email, "password", password),
                TokenResponse.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().accessToken()).isNotBlank();
        return response.getBody().accessToken();
    }

    public static String adminToken(TestRestTemplate rest) {
        return loginAccessToken(rest, ADMIN_EMAIL, ADMIN_PASSWORD);
    }

    public static String receptionToken(TestRestTemplate rest) {
        return loginAccessToken(rest, RECEPTION_EMAIL, RECEPTION_PASSWORD);
    }

    public static HttpHeaders bearerHeaders(String accessToken) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken);
        return headers;
    }

    public static <T> HttpEntity<T> bearer(String accessToken, T body) {
        return new HttpEntity<>(body, bearerHeaders(accessToken));
    }

    public static HttpEntity<Void> bearer(String accessToken) {
        return new HttpEntity<>(bearerHeaders(accessToken));
    }

    public static String extractRefreshCookie(ResponseEntity<?> response) {
        List<String> setCookie = response.getHeaders().get(HttpHeaders.SET_COOKIE);
        if (setCookie == null) {
            return null;
        }
        for (String header : setCookie) {
            if (header.startsWith(REFRESH_COOKIE + "=")) {
                String value = header.substring(REFRESH_COOKIE.length() + 1);
                int end = value.indexOf(';');
                return end >= 0 ? value.substring(0, end) : value;
            }
        }
        return null;
    }

    public static HttpHeaders cookieHeader(String refreshToken) {
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.COOKIE, REFRESH_COOKIE + "=" + refreshToken);
        return headers;
    }
}
