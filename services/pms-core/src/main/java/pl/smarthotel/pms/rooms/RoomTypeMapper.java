package pl.smarthotel.pms.rooms;

import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import pl.smarthotel.pms.common.mapping.MapStructConfig;

@Mapper(config = MapStructConfig.class)
public interface RoomTypeMapper {

    @Mapping(target = "currency", constant = "PLN")
    RoomTypeResponse toResponse(RoomTypeEntity entity);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "amenities", expression = "java(normalizeAmenities(request.amenities()))")
    @Mapping(target = "active", expression = "java(request.active() == null || request.active())")
    RoomTypeEntity toEntity(CreateRoomTypeRequest request);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "amenities", expression = "java(normalizeAmenities(request.amenities()))")
    void updateEntity(UpdateRoomTypeRequest request, @MappingTarget RoomTypeEntity entity);

    default java.util.List<String> normalizeAmenities(java.util.List<String> amenities) {
        return amenities == null ? java.util.List.of() : java.util.List.copyOf(amenities);
    }
}
