package pl.smarthotel.pms.common.web;

import static net.logstash.logback.argument.StructuredArguments.kv;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * One structured access log line per request (Phase 10 shared schema fields under {@code http.*}).
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class HttpAccessLogFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger("pl.smarthotel.http");

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path != null
                && (path.startsWith("/actuator")
                        || path.startsWith("/v3/api-docs")
                        || path.startsWith("/swagger"));
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        long start = System.nanoTime();
        try {
            filterChain.doFilter(request, response);
        } finally {
            long durationMs = (System.nanoTime() - start) / 1_000_000L;
            log.info(
                    "http_request",
                    kv("http.method", request.getMethod()),
                    kv("http.path", request.getRequestURI()),
                    kv("http.status", response.getStatus()),
                    kv("durationMs", durationMs));
        }
    }
}
