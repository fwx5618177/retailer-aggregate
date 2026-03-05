package com.searetailer.api.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Simple in-memory rate limiter using a fixed-window algorithm.
 *
 * <p>Limits: 100 requests per minute per client IP for /api/v1 endpoints.
 * Health, actuator, and swagger endpoints are exempt.
 * </p>
 *
 * <p>For production with multiple instances, replace with Redis-based
 * rate limiting (e.g. Bucket4j + Redis or Spring Cloud Gateway).</p>
 */
@Component
@Order(1) // After RequestIdFilter (HIGHEST_PRECEDENCE)
public class RateLimitFilter extends OncePerRequestFilter {

    private static final int MAX_REQUESTS_PER_MINUTE = 100;
    private static final long WINDOW_MS = 60_000L;

    private final ConcurrentHashMap<String, WindowCounter> counters = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        // Skip rate limiting for non-API endpoints
        return path.startsWith("/healthz")
            || path.startsWith("/actuator")
            || path.startsWith("/swagger-ui")
            || path.startsWith("/api-docs")
            || path.startsWith("/v3/api-docs")
            || path.startsWith("/h2-console");
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        String clientKey = resolveClientKey(request);
        WindowCounter counter = counters.compute(clientKey, (key, existing) -> {
            long now = System.currentTimeMillis();
            if (existing == null || now - existing.windowStart > WINDOW_MS) {
                return new WindowCounter(now);
            }
            return existing;
        });

        int current = counter.count.incrementAndGet();

        // Set rate limit headers
        response.setHeader("X-RateLimit-Limit", String.valueOf(MAX_REQUESTS_PER_MINUTE));
        response.setHeader("X-RateLimit-Remaining",
                String.valueOf(Math.max(0, MAX_REQUESTS_PER_MINUTE - current)));

        if (current > MAX_REQUESTS_PER_MINUTE) {
            long retryAfter = (counter.windowStart + WINDOW_MS - System.currentTimeMillis()) / 1000;
            response.setHeader("Retry-After", String.valueOf(Math.max(1, retryAfter)));
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);

            Map<String, Object> body = Map.of(
                "error", "rate_limit_exceeded",
                "message", "Too many requests. Please retry after " + retryAfter + " seconds.",
                "request_id", request.getHeader("X-Request-ID") != null
                        ? request.getHeader("X-Request-ID") : "unknown",
                "timestamp", OffsetDateTime.now(ZoneOffset.UTC).toString()
            );
            objectMapper.writeValue(response.getOutputStream(), body);
            return;
        }

        filterChain.doFilter(request, response);
    }

    private String resolveClientKey(HttpServletRequest request) {
        // Use X-Forwarded-For if behind a reverse proxy, otherwise remote address
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isEmpty()) {
            return forwarded.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    /**
     * Periodic cleanup of stale entries (called internally, not a scheduled task).
     * In production, use a TTL-based cache (Caffeine, Redis).
     */
    void cleanup() {
        long now = System.currentTimeMillis();
        counters.entrySet().removeIf(e -> now - e.getValue().windowStart > WINDOW_MS * 2);
    }

    private static class WindowCounter {
        final long windowStart;
        final AtomicInteger count;

        WindowCounter(long windowStart) {
            this.windowStart = windowStart;
            this.count = new AtomicInteger(0);
        }
    }
}
