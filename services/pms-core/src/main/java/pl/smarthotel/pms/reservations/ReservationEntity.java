package pl.smarthotel.pms.reservations;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import pl.smarthotel.pms.common.persistence.VersionedAuditedEntity;
import pl.smarthotel.pms.guests.GuestEntity;
import pl.smarthotel.pms.rooms.RoomEntity;

@Entity
@Table(name = "reservations", schema = "pms")
public class ReservationEntity extends VersionedAuditedEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "confirmation_code", nullable = false, unique = true, length = 12)
    private String confirmationCode;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "guest_id", nullable = false)
    private GuestEntity guest;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "room_id", nullable = false)
    private RoomEntity room;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "rate_plan_id", nullable = false)
    private RatePlanEntity ratePlan;

    @Column(name = "check_in", nullable = false)
    private LocalDate checkIn;

    @Column(name = "check_out", nullable = false)
    private LocalDate checkOut;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private ReservationStatus status = ReservationStatus.CONFIRMED;

    @Column(nullable = false)
    private short adults;

    @Column(name = "total_price", nullable = false, precision = 10, scale = 2)
    private BigDecimal totalPrice;

    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(nullable = false, length = 3)
    private String currency = "PLN";

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "price_breakdown", nullable = false, columnDefinition = "jsonb")
    private List<PriceBreakdownLine> priceBreakdown = new ArrayList<>();

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private ReservationSource source;

    public Long getId() {
        return id;
    }

    /** Package-visible for tests. */
    void setId(Long id) {
        this.id = id;
    }

    public String getConfirmationCode() {
        return confirmationCode;
    }

    public void setConfirmationCode(String confirmationCode) {
        this.confirmationCode = confirmationCode;
    }

    public GuestEntity getGuest() {
        return guest;
    }

    public void setGuest(GuestEntity guest) {
        this.guest = guest;
    }

    public RoomEntity getRoom() {
        return room;
    }

    public void setRoom(RoomEntity room) {
        this.room = room;
    }

    public RatePlanEntity getRatePlan() {
        return ratePlan;
    }

    public void setRatePlan(RatePlanEntity ratePlan) {
        this.ratePlan = ratePlan;
    }

    public LocalDate getCheckIn() {
        return checkIn;
    }

    public void setCheckIn(LocalDate checkIn) {
        this.checkIn = checkIn;
    }

    public LocalDate getCheckOut() {
        return checkOut;
    }

    public void setCheckOut(LocalDate checkOut) {
        this.checkOut = checkOut;
    }

    public ReservationStatus getStatus() {
        return status;
    }

    public void setStatus(ReservationStatus status) {
        this.status = status;
    }

    public short getAdults() {
        return adults;
    }

    public void setAdults(short adults) {
        this.adults = adults;
    }

    public BigDecimal getTotalPrice() {
        return totalPrice;
    }

    public void setTotalPrice(BigDecimal totalPrice) {
        this.totalPrice = totalPrice;
    }

    public String getCurrency() {
        return currency;
    }

    public void setCurrency(String currency) {
        this.currency = currency;
    }

    public List<PriceBreakdownLine> getPriceBreakdown() {
        return priceBreakdown;
    }

    public void setPriceBreakdown(List<PriceBreakdownLine> priceBreakdown) {
        this.priceBreakdown = priceBreakdown != null ? priceBreakdown : new ArrayList<>();
    }

    public ReservationSource getSource() {
        return source;
    }

    public void setSource(ReservationSource source) {
        this.source = source;
    }
}
