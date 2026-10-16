package pl.smarthotel.pms.pricing;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import java.lang.reflect.RecordComponent;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import pl.smarthotel.pms.pricing.dto.PricingDemandItem;
import pl.smarthotel.pms.pricing.dto.PricingEventItem;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuoteItemResponse;
import pl.smarthotel.pms.pricing.dto.PricingQuotesRequest;
import pl.smarthotel.pms.pricing.dto.PricingQuotesResponse;

/**
 * Drift guard: Java pricing DTOs must stay aligned with committed OpenAPI schemas.
 */
class PricingContractTest {

    private static OpenAPI openApi;

    @BeforeAll
    static void loadSpec() throws Exception {
        Path spec = resolveOpenApi();
        assertThat(Files.exists(spec)).as("OpenAPI file exists at %s", spec).isTrue();
        SwaggerParseResult result = new OpenAPIV3Parser().readLocation(spec.toUri().toString(), null, null);
        assertThat(result.getMessages()).isEmpty();
        openApi = result.getOpenAPI();
        assertThat(openApi).isNotNull();
        assertThat(openApi.getComponents().getSchemas()).isNotEmpty();
    }

    @Test
    void quotesRequestFieldsMatchSchema() {
        assertRecordMatchesSchema(PricingQuotesRequest.class, "QuotesRequest");
    }

    @Test
    void quoteItemRequestFieldsMatchSchema() {
        assertRecordMatchesSchema(PricingQuoteItemRequest.class, "QuoteItemRequest");
    }

    @Test
    void quotesResponseFieldsMatchSchema() {
        assertRecordMatchesSchema(PricingQuotesResponse.class, "QuotesResponse");
    }

    @Test
    void quoteItemResponseFieldsMatchSchema() {
        assertRecordMatchesSchema(PricingQuoteItemResponse.class, "QuoteItemResponse");
    }

    @Test
    void eventItemFieldsMatchSchema() {
        assertRecordMatchesSchema(PricingEventItem.class, "EventItem");
    }

    @Test
    void demandItemFieldsMatchSchema() {
        assertRecordMatchesSchema(PricingDemandItem.class, "DemandIndicatorItem");
    }

    @Test
    void openApiJsonIsParsableAndContainsExpectedPaths() throws Exception {
        Path spec = resolveOpenApi();
        JsonNode root = new ObjectMapper().readTree(Files.readString(spec));
        assertThat(root.path("paths").fieldNames())
                .toIterable()
                .anyMatch(p -> p.contains("/api/v1/quotes"));
        assertThat(root.path("paths").fieldNames())
                .toIterable()
                .anyMatch(p -> p.contains("/api/v1/events"));
    }

    private static void assertRecordMatchesSchema(Class<?> recordType, String schemaName) {
        Schema<?> schema = openApi.getComponents().getSchemas().get(schemaName);
        assertThat(schema).as("schema %s present", schemaName).isNotNull();
        Map<String, Schema> props = schema.getProperties();
        assertThat(props).isNotNull();

        Set<String> schemaFields = props.keySet().stream()
                .map(s -> s.toLowerCase(Locale.ROOT))
                .collect(Collectors.toSet());
        Set<String> javaFields = Stream.of(recordType.getRecordComponents())
                .map(RecordComponent::getName)
                .map(s -> s.toLowerCase(Locale.ROOT))
                .collect(Collectors.toSet());

        assertThat(javaFields)
                .as("%s components must equal OpenAPI %s properties (case-insensitive)", recordType.getSimpleName(), schemaName)
                .containsExactlyInAnyOrderElementsOf(schemaFields);
    }

    private static Path resolveOpenApi() {
        Path fromModule = Path.of("..", "..", "docs", "api", "pricing-openapi.json").normalize();
        if (Files.exists(fromModule)) {
            return fromModule.toAbsolutePath();
        }
        Path fromRepo = Path.of("docs", "api", "pricing-openapi.json");
        if (Files.exists(fromRepo)) {
            return fromRepo.toAbsolutePath();
        }
        return Path.of(System.getProperty("user.dir"))
                .resolve("../../docs/api/pricing-openapi.json")
                .normalize()
                .toAbsolutePath();
    }
}
