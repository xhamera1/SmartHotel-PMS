package pl.smarthotel.pms.common.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI pmsOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("SmartHotel PMS Core API")
                        .description("Public booking and admin endpoints — contract: docs/api/pms-api.md")
                        .version("v1"));
    }
}
