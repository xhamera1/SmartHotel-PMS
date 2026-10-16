package pl.smarthotel.pms.pricing.dto;

import java.util.List;
import java.util.UUID;

public record PricingQuotesRequest(UUID requestId, String currency, List<PricingQuoteItemRequest> items) {

    public PricingQuotesRequest(UUID requestId, List<PricingQuoteItemRequest> items) {
        this(requestId, "PLN", items);
    }
}
