package pl.smarthotel.pms.auth;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.JwsHeader;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtClaimsSet;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtEncoderParameters;
import org.springframework.security.oauth2.jwt.JwtException;
import org.springframework.stereotype.Service;
import pl.smarthotel.pms.common.exception.ApplicationException;

@Service
public class JwtTokenService {

    public static final String CLAIM_TOKEN_USE = "token_use";
    public static final String CLAIM_ROLES = "roles";
    public static final String TOKEN_USE_ACCESS = "access";
    public static final String TOKEN_USE_REFRESH = "refresh";

    private final JwtEncoder jwtEncoder;
    private final JwtDecoder jwtDecoder;
    private final Clock clock;
    private final long accessTtlSeconds;
    private final long refreshTtlSeconds;

    public JwtTokenService(
            JwtEncoder jwtEncoder,
            JwtDecoder jwtDecoder,
            Clock clock,
            @Value("${app.jwt.access-token-ttl:3600}") long accessTtlSeconds,
            @Value("${app.jwt.refresh-token-ttl:86400}") long refreshTtlSeconds) {
        this.jwtEncoder = jwtEncoder;
        this.jwtDecoder = jwtDecoder;
        this.clock = clock;
        this.accessTtlSeconds = accessTtlSeconds;
        this.refreshTtlSeconds = refreshTtlSeconds;
    }

    public IssuedTokens issue(StaffUserEntity staff) {
        Instant now = clock.instant();
        String access = encode(staff, TOKEN_USE_ACCESS, now, accessTtlSeconds);
        String refresh = encode(staff, TOKEN_USE_REFRESH, now, refreshTtlSeconds);
        return new IssuedTokens(access, refresh, accessTtlSeconds);
    }

    /** Validates a refresh JWT and returns its subject (staff email). */
    public String subjectFromRefreshToken(String refreshToken) {
        Jwt jwt;
        try {
            jwt = jwtDecoder.decode(refreshToken);
        } catch (JwtException ex) {
            throw ApplicationException.unauthorized("Invalid refresh token");
        }
        if (!TOKEN_USE_REFRESH.equals(jwt.getClaimAsString(CLAIM_TOKEN_USE))) {
            throw ApplicationException.unauthorized("Refresh token required");
        }
        return jwt.getSubject();
    }

    public long accessTtlSeconds() {
        return accessTtlSeconds;
    }

    private String encode(StaffUserEntity staff, String tokenUse, Instant now, long ttlSeconds) {
        JwtClaimsSet claims = JwtClaimsSet.builder()
                .issuer("smarthotel-pms")
                .issuedAt(now)
                .expiresAt(now.plusSeconds(ttlSeconds))
                .subject(staff.getEmail())
                .claim(CLAIM_TOKEN_USE, tokenUse)
                .claim(CLAIM_ROLES, List.of(staff.getRole().name()))
                .claim("name", staff.getFullName())
                .build();
        JwsHeader header = JwsHeader.with(MacAlgorithm.HS256).build();
        return jwtEncoder.encode(JwtEncoderParameters.from(header, claims)).getTokenValue();
    }

    public record IssuedTokens(String accessToken, String refreshToken, long expiresIn) {}
}
