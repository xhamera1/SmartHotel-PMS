package pl.smarthotel.pms.auth;

public record TokenResponse(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn,
        String email,
        String fullName,
        StaffRole role) {}
