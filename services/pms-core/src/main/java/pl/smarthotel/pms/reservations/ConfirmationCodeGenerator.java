package pl.smarthotel.pms.reservations;

import java.util.random.RandomGenerator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 8-character confirmation codes from an unambiguous alphabet (no {@code 0/O/1/I/L}).
 * Collision-checked against existing reservations before return.
 */
@Component
public class ConfirmationCodeGenerator {

    /** Unambiguous uppercase set — no 0/O, 1/I, or L (look-alike glyphs). */
    public static final String ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";

    private static final int LENGTH = 8;
    private static final int MAX_ATTEMPTS = 32;

    private final ReservationRepository reservationRepository;
    private final RandomGenerator random;

    @Autowired
    public ConfirmationCodeGenerator(ReservationRepository reservationRepository) {
        this(reservationRepository, RandomGenerator.getDefault());
    }

    ConfirmationCodeGenerator(ReservationRepository reservationRepository, RandomGenerator random) {
        this.reservationRepository = reservationRepository;
        this.random = random;
    }

    public String next() {
        for (int attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
            String code = generate();
            if (!reservationRepository.existsByConfirmationCode(code)) {
                return code;
            }
        }
        throw new IllegalStateException(
                "Unable to allocate a unique confirmation code after " + MAX_ATTEMPTS + " attempts");
    }

    private String generate() {
        char[] chars = new char[LENGTH];
        for (int i = 0; i < LENGTH; i++) {
            chars[i] = ALPHABET.charAt(random.nextInt(ALPHABET.length()));
        }
        return new String(chars);
    }
}
