package pl.smarthotel.pms.guests;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import pl.smarthotel.pms.common.mapping.MapStructConfig;

@Mapper(config = MapStructConfig.class)
public interface GuestMapper {

    GuestResponse toResponse(GuestEntity entity);

    @Mapping(target = "id", ignore = true)
    GuestEntity toEntity(CreateGuestRequest request);

    @Mapping(target = "id", ignore = true)
    void updateEntity(UpdateGuestRequest request, @MappingTarget GuestEntity entity);

    @Mapping(target = "id", ignore = true)
    void applyUpsert(GuestUpsertRequest request, @MappingTarget GuestEntity entity);
}
