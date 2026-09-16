package pl.smarthotel.pms.reservations;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

import java.util.HashSet;
import java.util.Set;
import java.util.random.RandomGenerator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ConfirmationCodeGeneratorTest {

    @Mock
    private ReservationRepository reservationRepository;

    @Mock
    private RandomGenerator random;

    @Test
    void shouldGenerateEightCharCodesFromUnambiguousAlphabet() {
        when(reservationRepository.existsByConfirmationCode(anyString())).thenReturn(false);
        when(random.nextInt(anyInt())).thenReturn(0, 1, 2, 3, 4, 5, 6, 7);

        String code = new ConfirmationCodeGenerator(reservationRepository, random).next();

        assertThat(code).hasSize(8);
        assertThat(code).matches("[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{8}");
        assertThat(code).doesNotContain("0", "O", "1", "I", "L");
    }

    @Test
    void shouldRetryOnCollisionUntilUnique() {
        when(reservationRepository.existsByConfirmationCode("22222222")).thenReturn(true);
        when(reservationRepository.existsByConfirmationCode("33333333")).thenReturn(false);
        // First attempt all index 0 → '2'; second attempt all index 1 → '3'
        when(random.nextInt(anyInt()))
                .thenReturn(0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1);

        String code = new ConfirmationCodeGenerator(reservationRepository, random).next();

        assertThat(code).isEqualTo("33333333");
    }

    @Test
    void shouldFailAfterTooManyCollisions() {
        when(reservationRepository.existsByConfirmationCode(anyString())).thenReturn(true);
        when(random.nextInt(anyInt())).thenReturn(0);

        assertThatThrownBy(() -> new ConfirmationCodeGenerator(reservationRepository, random).next())
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("confirmation code");
    }

    @Test
    void alphabetExcludesAmbiguousGlyphs() {
        Set<Character> alphabet = new HashSet<>();
        for (char c : ConfirmationCodeGenerator.ALPHABET.toCharArray()) {
            alphabet.add(c);
        }
        assertThat(alphabet).doesNotContain('0', 'O', '1', 'I', 'L');
        assertThat(ConfirmationCodeGenerator.ALPHABET).hasSizeGreaterThanOrEqualTo(30);
    }
}
