package pl.smarthotel.pms.rooms;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import pl.smarthotel.pms.common.mapping.MapStructConfig;

@Mapper(config = MapStructConfig.class)
public interface RoomMapper {

    @Mapping(target = "roomTypeId", source = "roomType.id")
    @Mapping(target = "roomTypeCode", source = "roomType.code")
    RoomResponse toResponse(RoomEntity entity);
}
