package pl.smarthotel.pms.common.money;

import java.math.BigDecimal;

/** API money representation — always PLN for this thesis (ADR-0009). */
public record MoneyResponse(BigDecimal amount, String currency) {

    public static MoneyResponse pln(BigDecimal amount) {
        return new MoneyResponse(amount, "PLN");
    }
}
