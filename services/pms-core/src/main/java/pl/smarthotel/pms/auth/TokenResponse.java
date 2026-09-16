package pl.smarthotel.pms.auth;

/**
 * Access-token payload for the SPA. The refresh JWT is delivered only via an
 * httpOnly cookie (ADR-0014), never in this JSON body.
 */
public record TokenResponse(
        String accessToken,
        String tokenType,
        long expiresIn,
        String email,
        String fullName,
        StaffRole role) {}
