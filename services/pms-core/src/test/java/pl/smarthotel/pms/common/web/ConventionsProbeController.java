package pl.smarthotel.pms.common.web;

import io.swagger.v3.oas.annotations.Hidden;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import pl.smarthotel.pms.common.exception.ApplicationException;

/** Test-only controller used by {@link ConventionsWebTest}. Hidden from OpenAPI. */
@Hidden
@RestController
class ConventionsProbeController {

    @GetMapping("/probe/ok")
    String ok() {
        return "ok";
    }

    @GetMapping("/probe/missing")
    String missing() {
        throw ApplicationException.notFound("Room type STD not found");
    }

    @PostMapping("/probe/echo")
    EchoResponse echo(@Valid @RequestBody EchoRequest request) {
        return new EchoResponse(request.name());
    }

    record EchoRequest(@NotBlank @Size(max = 40) String name) {}

    record EchoResponse(String name) {}
}
