package pl.smarthotel.pms.common.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(
        controllers = ConventionsProbeController.class,
        excludeAutoConfiguration = SecurityAutoConfiguration.class)
@Import({GlobalExceptionHandler.class, CorrelationIdFilter.class})
class ConventionsWebTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void echoesProvidedRequestId() throws Exception {
        mockMvc.perform(get("/probe/ok").header(CorrelationIds.HEADER, "client-req-1"))
                .andExpect(status().isOk())
                .andExpect(header().string(CorrelationIds.HEADER, "client-req-1"));
    }

    @Test
    void generatesRequestIdWhenMissing() throws Exception {
        String echoed = mockMvc.perform(get("/probe/ok"))
                .andExpect(status().isOk())
                .andExpect(header().exists(CorrelationIds.HEADER))
                .andReturn()
                .getResponse()
                .getHeader(CorrelationIds.HEADER);

        assertThat(echoed).isNotBlank();
    }

    @Test
    void validationErrorsReturnProblemJson() throws Exception {
        mockMvc.perform(post("/probe/echo")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(ProblemTypes.VALIDATION_ERROR))
                .andExpect(jsonPath("$.title").value("Validation failed"))
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.errors[0].field").value("name"));
    }

    @Test
    void applicationExceptionReturnsProblemJson() throws Exception {
        mockMvc.perform(get("/probe/missing"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.type").value(ProblemTypes.NOT_FOUND))
                .andExpect(jsonPath("$.title").value("Not found"))
                .andExpect(jsonPath("$.detail").value("Room type STD not found"))
                .andExpect(jsonPath("$.instance").value("/probe/missing"));
    }
}
