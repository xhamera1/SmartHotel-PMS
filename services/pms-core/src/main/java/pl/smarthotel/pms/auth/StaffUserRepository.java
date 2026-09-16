package pl.smarthotel.pms.auth;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StaffUserRepository extends JpaRepository<StaffUserEntity, Long> {

    Optional<StaffUserEntity> findByEmailIgnoreCase(String email);
}
