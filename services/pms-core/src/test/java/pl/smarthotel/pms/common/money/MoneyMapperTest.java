package pl.smarthotel.pms.common.money;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;

class MoneyMapperTest {

    private final MoneyMapper mapper = Mappers.getMapper(MoneyMapper.class);

    @Test
    void mapsAmountToPlnMoneyResponse() {
        MoneyResponse money = mapper.toPln(new BigDecimal("612.00"));

        assertThat(money.amount()).isEqualByComparingTo("612.00");
        assertThat(money.currency()).isEqualTo("PLN");
    }
}
