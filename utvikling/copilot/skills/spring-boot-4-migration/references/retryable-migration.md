# Resilience: spring-retry / resilience4j @Retry → Spring native @Retryable

Spring Framework 7 has native `@Retryable` (`org.springframework.resilience.annotation`). This replaces **both** spring-retry's `@Retryable` and resilience4j's `@Retry`.

**Note**: There is no native Spring circuit breaker yet. Keep resilience4j `@CircuitBreaker` for that.

## Setup

```java
// Replace @EnableRetry (spring-retry) with:
@EnableResilientMethods
@SpringBootApplication
public class Application { ... }
```

```xml
<!-- Required for AOP proxies -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aspectj</artifactId>
</dependency>

<!-- Remove spring-retry dependency -->
<!-- <dependency>
    <groupId>org.springframework.retry</groupId>
    <artifactId>spring-retry</artifactId>
</dependency> -->
```

## Migrating from spring-retry

The native `@Retryable` flattens `@Backoff` attributes directly onto the annotation. Key attribute mapping:

| spring-retry | Spring native | Notes |
|---|---|---|
| `retryFor = X.class` | `includes = X.class` | |
| `exclude = X.class` | `excludes = X.class` | |
| `maxAttempts = N` | `maxRetries = N - 1` | spring-retry counts total attempts (initial + retries), native counts only retries |
| `@Backoff(delay = 1000)` | `delay = 1000` | Default is 1000ms in both |
| `@Backoff(multiplier = 2)` | `multiplier = 2` | Default: spring-retry=0 (no multiplier), native=1.0 (same effect) |
| `@Backoff(maxDelay = 5000)` | `maxDelay = 5000` | |

**⚠️ maxAttempts vs maxRetries**: spring-retry `maxAttempts = 3` (default) = 1 initial + 2 retries. Native `maxRetries` default = 3 retries = 4 total attempts. To preserve spring-retry's default behavior, explicitly set `maxRetries = 2`.

Examples:

```java
// Before (spring-retry)
@Retryable(retryFor = MyException.class, backoff = @Backoff(delay = 1000, multiplier = 2))
// After (Spring native) — maxAttempts 3 (default) → maxRetries 2
@Retryable(includes = MyException.class, maxRetries = 2, delay = 1000, multiplier = 2)
```

```java
// Before (spring-retry)
@Retryable(retryFor = MyException.class, maxAttempts = 5, backoff = @Backoff(delay = 200))

// After (Spring native) — maxAttempts 5 → maxRetries 4
@Retryable(includes = MyException.class, maxRetries = 4, delay = 200)
```

```java
// Before (spring-retry, no @Backoff = default 1000ms delay)
@Retryable(retryFor = MyException.class)

// After (Spring native) — delay defaults to 1000, same as spring-retry
@Retryable(includes = MyException.class, maxRetries = 2)
```

## Migrating RetryListener

spring-retry's `RetryListener` is replaced by Spring's `@EventListener` for `MethodRetryEvent`:

```java
// Before (spring-retry)
@Component
public class RetryLogger implements RetryListener {
    @Override
    public <T, E extends Throwable> void onError(RetryContext context, RetryCallback<T, E> callback, Throwable throwable) {
        log.warn("Retry {} failed: {}", context.getRetryCount(), throwable.getMessage());
    }
}

// After (Spring native)
import org.springframework.core.retry.RetryException; // note: in spring-core
import org.springframework.resilience.retry.MethodRetryEvent; // note: in spring-context

@Component
public class RetryLogger {
    @EventListener
    public void onRetry(MethodRetryEvent event) {
        Throwable cause = (event.getFailure() instanceof RetryException re) ? re.getCause() : event.getFailure();
        log.warn("Retry for {} failed: {}", event.getMethod().getName(), cause.getMessage(), cause);
    }
}
```

`MethodRetryEvent` extends `ApplicationEvent` and provides `getMethod()`, `getFailure()`, and `isRetryAborted()`. Note: retry count is not directly available (unlike spring-retry's `RetryContext`).

> **Important:** `MethodRetryEvent.getFailure()` wraps the original exception in a `org.springframework.core.retry.RetryException`. Use `getCause()` to access the original exception. The old spring-retry `RetryListener.onError()` provided the raw throwable directly, but the new event-based approach wraps it.

## Migrating from resilience4j @Retry

```java
// Before (resilience4j)
@Retry(name = "my-service")

// After (Spring native)
@Retryable(includes = MyTechnicalException.class)
```

Remove resilience4j retry configuration from `application.properties`:
```properties
# Delete these
resilience4j.retry.instances.my-service.max-attempts=3
resilience4j.retry.instances.my-service.wait-duration=500ms
resilience4j.retry.instances.my-service.retry-exceptions=...
```

## Aspect ordering

When combining resilience4j `@CircuitBreaker` with Spring `@Retryable`:
- Circuit breaker is the **outer** aspect (wraps retry)
- Each method invocation = 1 circuit breaker call, regardless of retries
- This matches the default behavior when both were resilience4j annotations

## Dependencies

```xml
<!-- Remove both -->
<!-- <dependency>org.springframework.retry:spring-retry</dependency> -->
<!-- <dependency>io.github.resilience4j:resilience4j-reactor</dependency> -->

<!-- Keep for @CircuitBreaker — use resilience4j-spring-boot4 (not yet in resilience4j-bom, declare version explicitly) -->
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot4</artifactId>
</dependency>
```
