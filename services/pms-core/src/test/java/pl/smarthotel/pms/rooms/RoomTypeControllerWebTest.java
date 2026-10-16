package pl.smarthotel.pms.rooms;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import pl.smarthotel.pms.common.web.CorrelationIdFilter;
import pl.smarthotel.pms.common.web.GlobalExceptionHandler;
import pl.smarthotel.pms.common.web.PageResponse;
import pl.smarthotel.pms.common.web.ProblemTypes;

@WebMvcTest(controllers = RoomTypeController.class)
@Import({GlobalExceptionHandler.class, CorrelationIdFilter.class,
        RoomTypeControllerWebTest.MethodSecurityTestConfig.class})
class RoomTypeControllerWebTest {

    @TestConfiguration
    @EnableMethodSecurity
    static class MethodSecurityTestConfig {}


    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private RoomTypeService roomTypeService;

    // --- Validation tests ---

    @Test
    @WithMockUser(roles = "ADMIN")
    void createWithBlankCode_returns400WithValidationError() throws Exception {
        mockMvc.perform(post("/api/v1/admin/room-types")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"code":"","name":"Deluxe","capacity":2,
                                 "basePrice":420,"minPrice":300,"maxPrice":800}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(ProblemTypes.VALIDATION_ERROR))
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.errors").isArray());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void createWithInvalidPriceBand_returns400() throws Exception {
        mockMvc.perform(post("/api/v1/admin/room-types")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"code":"ERR","name":"Bad Price","capacity":2,
                                 "basePrice":100,"minPrice":200,"maxPrice":800}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(ProblemTypes.VALIDATION_ERROR));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void createWithMissingRequired_returns400() throws Exception {
        mockMvc.perform(post("/api/v1/admin/room-types")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(ProblemTypes.VALIDATION_ERROR))
                .andExpect(jsonPath("$.errors").isArray());
    }

    // --- Security matrix tests ---

    @Test
    void anonymousGetList_returns401() throws Exception {
        mockMvc.perform(get("/api/v1/admin/room-types"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void anonymousCreate_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/admin/room-types")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"code":"NEW","name":"New","capacity":2,
                                 "basePrice":250,"minPrice":180,"maxPrice":450}
                                """))
                .andExpect(status().isUnauthorized());
    }

    @ParameterizedTest
    @CsvSource({"ADMIN, 200", "RECEPTIONIST, 200"})
    @WithMockUser
    void listAllowedForAdminAndReceptionist(String role) throws Exception {
        given(roomTypeService.list(any(), any(), any(int.class), any(int.class)))
                .willReturn(new PageResponse<>(List.of(), new PageResponse.PageMeta(0, 20, 0, 0)));

        mockMvc.perform(get("/api/v1/admin/room-types")
                        .with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user("u").roles(role)))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "RECEPTIONIST")
    void receptionistCannotCreate_returns403() throws Exception {
        mockMvc.perform(post("/api/v1/admin/room-types")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"code":"NEW","name":"New","capacity":2,
                                 "basePrice":250,"minPrice":180,"maxPrice":450}
                                """))
                .andExpect(status().isForbidden());
    }

    // --- Serialization test ---

    @Test
    @WithMockUser(roles = "ADMIN")
    void validCreate_returnsCreatedWithCorrectSerialization() throws Exception {
        RoomTypeResponse response = new RoomTypeResponse(
                1L, "DLX", "Deluxe", "Nice room", (short) 2,
                new BigDecimal("420.00"), new BigDecimal("300.00"), new BigDecimal("800.00"),
                "PLN", List.of("wifi", "minibar"), true,
                Instant.parse("2026-10-01T10:00:00Z"), Instant.parse("2026-10-01T10:00:00Z"));
        given(roomTypeService.create(any())).willReturn(response);

        mockMvc.perform(post("/api/v1/admin/room-types")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"code":"DLX","name":"Deluxe","description":"Nice room",
                                 "capacity":2,"basePrice":420,"minPrice":300,"maxPrice":800,
                                 "amenities":["wifi","minibar"]}
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.code").value("DLX"))
                .andExpect(jsonPath("$.basePrice").value(420.00));
    }
}
