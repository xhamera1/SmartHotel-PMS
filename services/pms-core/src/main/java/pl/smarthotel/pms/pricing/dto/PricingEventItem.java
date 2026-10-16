package pl.smarthotel.pms.pricing.dto;

public record PricingEventItem(
        long id,
        String name,
        String category,
        String startsAt,
        String endsAt,
        Integer impactScore,
        Double distanceKm) {}
