package pl.smarthotel.pms.pricing;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
@EnableCaching
@EnableConfigurationProperties(PricingProperties.class)
public class PricingClientConfig {

    private static final Logger log = LoggerFactory.getLogger(PricingClientConfig.class);

    /**
     * Uses Spring Boot's {@link RestClient.Builder} so Jackson serializes {@code LocalDate}
     * as ISO-8601 strings (not arrays) — required by pricing-service Pydantic schemas.
     */
    @Bean(name = "pricingRestClient")
    RestClient pricingRestClient(RestClient.Builder restClientBuilder, PricingProperties properties) {
        log.info(
                "Pricing client baseUrl={} apiKey={} enabled={}",
                properties.baseUrl(),
                properties.maskedApiKey(),
                properties.enabled());

        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.connectTimeoutMs());
        requestFactory.setReadTimeout(properties.batchReadTimeoutMs());

        return restClientBuilder
                .baseUrl(properties.baseUrl())
                .defaultHeader("X-Internal-Api-Key", properties.apiKey())
                .defaultHeader("Content-Type", "application/json")
                .requestFactory(requestFactory)
                .build();
    }

    /**
     * A second RestClient with a shorter read timeout for on-demand single-item
     * quotes during the booking path (plan D6: 2 s budget).
     */
    @Bean(name = "pricingOnDemandRestClient")
    RestClient pricingOnDemandRestClient(RestClient.Builder restClientBuilder, PricingProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.connectTimeoutMs());
        requestFactory.setReadTimeout(properties.onDemandTimeoutMs());

        return restClientBuilder
                .baseUrl(properties.baseUrl())
                .defaultHeader("X-Internal-Api-Key", properties.apiKey())
                .defaultHeader("Content-Type", "application/json")
                .requestFactory(requestFactory)
                .build();
    }
}
