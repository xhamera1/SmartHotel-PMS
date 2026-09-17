package pl.smarthotel.pms.pricing;

public record PricingRefreshResponse(String status, String message, int daysUpdated) {}
