package pl.smarthotel.pms.common.mapping;

import org.mapstruct.MapperConfig;
import org.mapstruct.ReportingPolicy;

/**
 * Shared MapStruct defaults: Spring component model, fail on unmapped targets so
 * entity ↔ DTO drift is caught at compile time.
 */
@MapperConfig(componentModel = "spring", unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface MapStructConfig {}
