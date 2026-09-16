package pl.smarthotel.pms.common.money;

import java.math.BigDecimal;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import pl.smarthotel.pms.common.mapping.MapStructConfig;

@Mapper(config = MapStructConfig.class)
public interface MoneyMapper {

    @Mapping(target = "amount", source = ".")
    @Mapping(target = "currency", constant = "PLN")
    MoneyResponse toPln(BigDecimal amount);
}
