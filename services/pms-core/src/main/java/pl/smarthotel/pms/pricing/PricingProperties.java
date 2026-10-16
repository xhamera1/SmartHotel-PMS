package pl.smarthotel.pms.pricing;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.pricing")
public record PricingProperties(
        boolean enabled,
        String baseUrl,
        String apiKey,
        int connectTimeoutMs,
        int readTimeoutMs,
        int batchReadTimeoutMs,
        int refreshHorizonDays,
        int refreshChunkSize,
        int onDemandTimeoutMs) {

    public PricingProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "http://localhost:8081";
        }
        if (apiKey == null) {
            apiKey = "";
        }
        if (connectTimeoutMs <= 0) {
            connectTimeoutMs = 1000;
        }
        if (readTimeoutMs <= 0) {
            readTimeoutMs = 3000;
        }
        if (batchReadTimeoutMs <= 0) {
            batchReadTimeoutMs = 10000;
        }
        if (refreshHorizonDays <= 0) {
            refreshHorizonDays = 180;
        }
        if (refreshChunkSize <= 0) {
            refreshChunkSize = 366;
        }
        if (onDemandTimeoutMs <= 0) {
            onDemandTimeoutMs = 2000;
        }
    }

    public String maskedApiKey() {
        if (apiKey == null || apiKey.isBlank()) {
            return "(empty)";
        }
        if (apiKey.length() <= 4) {
            return "****";
        }
        return "****" + apiKey.substring(apiKey.length() - 4);
    }
}
