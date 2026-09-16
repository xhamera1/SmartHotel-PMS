package pl.smarthotel.pms.auth;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import pl.smarthotel.pms.common.exception.ApplicationException;

/** Simple in-memory login rate limiter (bucket4j) — Optional-Advanced in Phase 2 step 8. */
@Component
public class LoginRateLimiter {

    private final ConcurrentHashMap<String, Bucket> buckets = new ConcurrentHashMap<>();
    private final int capacity;
    private final Duration window;

    public LoginRateLimiter(
            @Value("${app.auth.login-rate-limit.capacity:10}") int capacity,
            @Value("${app.auth.login-rate-limit.window:PT1M}") Duration window) {
        this.capacity = capacity;
        this.window = window;
    }

    public void check(String clientKey) {
        Bucket bucket = buckets.computeIfAbsent(clientKey, key -> Bucket.builder()
                .addLimit(Bandwidth.builder()
                        .capacity(capacity)
                        .refillGreedy(capacity, window)
                        .build())
                .build());
        if (!bucket.tryConsume(1)) {
            throw ApplicationException.tooManyRequests(
                    "Too many login attempts — try again in a minute");
        }
    }
}
