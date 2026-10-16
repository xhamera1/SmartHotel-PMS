package pl.smarthotel.pms.reservations;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import pl.smarthotel.pms.common.mapping.MapStructConfig;
import pl.smarthotel.pms.guests.GuestEntity;

@Mapper(config = MapStructConfig.class)
public interface ReservationMapper {

    @Mapping(target = "roomType", source = "room.roomType.code")
    @Mapping(target = "roomNumber", source = "room.roomNumber")
    @Mapping(target = "ratePlan", source = "ratePlan")
    ReservationResponse toResponse(ReservationEntity entity);

    @Mapping(target = "code", source = "code")
    @Mapping(target = "refundable", source = "refundable")
    @Mapping(target = "breakfastIncluded", source = "breakfastIncluded")
    ReservationResponse.RatePlanSummary toRatePlanSummary(RatePlanEntity entity);

    @Mapping(target = "roomType", source = "room.roomType.code")
    @Mapping(target = "roomNumber", source = "room.roomNumber")
    @Mapping(target = "guestName", expression = "java(entity.getGuest().getFirstName() + \" \" + entity.getGuest().getLastName())")
    @Mapping(target = "guestEmail", source = "guest.email")
    AdminReservationSummary toAdminSummary(ReservationEntity entity);
}
