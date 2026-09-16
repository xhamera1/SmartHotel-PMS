package pl.smarthotel.pms.auth;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.smarthotel.pms.common.exception.ApplicationException;

@Service
@Transactional(readOnly = true)
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final StaffUserRepository staffUserRepository;
    private final JwtTokenService jwtTokenService;

    public AuthService(
            AuthenticationManager authenticationManager,
            StaffUserRepository staffUserRepository,
            JwtTokenService jwtTokenService) {
        this.authenticationManager = authenticationManager;
        this.staffUserRepository = staffUserRepository;
        this.jwtTokenService = jwtTokenService;
    }

    public SessionTokens login(LoginRequest request) {
        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(
                            request.email().trim(), request.password()));
        } catch (BadCredentialsException | DisabledException ex) {
            throw ApplicationException.unauthorized("Invalid email or password");
        } catch (AuthenticationException ex) {
            throw ApplicationException.unauthorized("Authentication failed");
        }

        StaffUserEntity staff = requireActiveStaff(request.email().trim());
        return issueSession(staff);
    }

    public SessionTokens refresh(String refreshToken) {
        String email = jwtTokenService.subjectFromRefreshToken(refreshToken.trim());
        StaffUserEntity staff = requireActiveStaff(email);
        return issueSession(staff);
    }

    private SessionTokens issueSession(StaffUserEntity staff) {
        JwtTokenService.IssuedTokens tokens = jwtTokenService.issue(staff);
        TokenResponse access = new TokenResponse(
                tokens.accessToken(),
                "Bearer",
                tokens.expiresIn(),
                staff.getEmail(),
                staff.getFullName(),
                staff.getRole());
        return new SessionTokens(access, tokens.refreshToken());
    }

    private StaffUserEntity requireActiveStaff(String email) {
        return staffUserRepository
                .findByEmailIgnoreCase(email)
                .filter(StaffUserEntity::isActive)
                .orElseThrow(() -> ApplicationException.unauthorized("Invalid email or password"));
    }

    /** Access payload for JSON + refresh JWT for the httpOnly cookie. */
    public record SessionTokens(TokenResponse access, String refreshToken) {}
}
