package pl.smarthotel.pms.common.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.tags.Tag;
import java.util.List;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    public static final String BEARER_JWT = "bearer-jwt";

    @Bean
    OpenAPI pmsOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("SmartHotel PMS Core API")
                        .description(
                                """
                                Public booking and staff admin API.

                                Error contract: RFC 7807 `application/problem+json` \
                                (`https://smarthotel/problems/…`). Full catalog: `docs/api/pms-api.md`.
                                """)
                        .version("v1")
                        .contact(new Contact().name("SmartHotel-PMS").url("https://github.com"))
                        .license(new License().name("MIT")))
                .servers(List.of(new Server().url("/").description("Current host")))
                .tags(List.of(
                        new Tag().name("Auth").description("Staff login and token refresh"),
                        new Tag().name("Availability").description("Public inventory search"),
                        new Tag().name("Reservations").description("Public booking create / lookup / cancel"),
                        new Tag().name("Admin — Room types").description("ADMIN only"),
                        new Tag().name("Admin — Rooms").description("ADMIN only"),
                        new Tag().name("Admin — Guests").description("ADMIN or RECEPTIONIST"),
                        new Tag().name("Admin — Reservations").description("ADMIN or RECEPTIONIST")))
                .components(new Components()
                        .addSecuritySchemes(
                                BEARER_JWT,
                                new SecurityScheme()
                                        .name(BEARER_JWT)
                                        .type(SecurityScheme.Type.HTTP)
                                        .scheme("bearer")
                                        .bearerFormat("JWT")
                                        .description(
                                                "Staff access token from POST /api/v1/auth/login "
                                                        + "(HS256, ~60 min). Refresh tokens are not accepted here.")));
    }
}
