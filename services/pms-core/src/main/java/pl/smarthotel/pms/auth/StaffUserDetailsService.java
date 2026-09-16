package pl.smarthotel.pms.auth;

import java.util.List;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class StaffUserDetailsService implements UserDetailsService {

    private final StaffUserRepository staffUserRepository;

    public StaffUserDetailsService(StaffUserRepository staffUserRepository) {
        this.staffUserRepository = staffUserRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        StaffUserEntity staff = staffUserRepository
                .findByEmailIgnoreCase(username.trim())
                .orElseThrow(() -> new UsernameNotFoundException("Unknown staff user"));
        return User.builder()
                .username(staff.getEmail())
                .password(staff.getPasswordHash())
                .disabled(!staff.isActive())
                .authorities(List.of(new SimpleGrantedAuthority("ROLE_" + staff.getRole().name())))
                .build();
    }
}
