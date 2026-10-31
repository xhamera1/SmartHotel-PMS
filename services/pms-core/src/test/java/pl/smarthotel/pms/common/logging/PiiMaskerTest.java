package pl.smarthotel.pms.common.logging;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class PiiMaskerTest {

    @Test
    void masksLocalPartKeepingDomain() {
        assertThat(PiiMasker.maskEmail("alice@example.com")).isEqualTo("a***@example.com");
    }

    @Test
    void returnsNullForBlank() {
        assertThat(PiiMasker.maskEmail("  ")).isNull();
        assertThat(PiiMasker.maskEmail(null)).isNull();
    }

    @Test
    void masksMalformedAsStars() {
        assertThat(PiiMasker.maskEmail("not-an-email")).isEqualTo("***");
    }
}
