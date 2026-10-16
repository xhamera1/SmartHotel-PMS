package pl.smarthotel.pms.pricing.dto;

import java.util.List;

public record PricingQuotesResponse(String modelVersion, List<PricingQuoteItemResponse> items) {}
