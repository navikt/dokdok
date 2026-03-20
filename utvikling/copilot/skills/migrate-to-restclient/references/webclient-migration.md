# WebClient → RestClient Migration

## Key differences

| WebClient (reactive) | RestClient (synchronous) |
|---|---|
| Returns `Mono<T>` / `Flux<T>` | Returns `T` directly |
| `.exchangeToMono()` / `.exchangeToFlux()` | `.exchange()` |
| `.retrieve().bodyToMono(T.class)` | `.retrieve().body(T.class)` |
| `ExchangeFilterFunction` | `ClientHttpRequestInterceptor` |
| `WebClient.Builder` | `RestClient.Builder` |
| Error via `WebClientResponseException` | Error via `HttpClientErrorException` / `HttpServerErrorException` |

## Basic migration pattern

### Before (WebClient)

```java
@Component
public class MyConsumer {
    private final WebClient webClient;

    public MyConsumer(@Qualifier("azureOauth2WebClient") WebClient webClient,
                      AppProperties props) {
        this.webClient = webClient.mutate()
                .baseUrl(props.getMyService().getUrl())
                .build();
    }

    public MyResponse fetchData(String id) {
        return webClient.get()
                .uri("/{id}", id)
                .header("Nav-Call-Id", MDC.get("callId"))
                .retrieve()
                .bodyToMono(MyResponse.class)
                .block();
    }
}
```

### After (RestClient)

```java
@Component
public class MyConsumer {
    private final RestClient restClient;
    private final String targetScope;

    public MyConsumer(RestClient restClientTexas, AppProperties props) {
        this.restClient = restClientTexas.mutate()
                .baseUrl(props.getMyService().getUrl())
                .build();
        this.targetScope = props.getMyService().getScope();
    }

    public MyResponse fetchData(String id) {
        return restClient.get()
                .uri("/{id}", id)
                .attribute(NaisTexasRequestInterceptor.TARGET_SCOPE, targetScope)
                .retrieve()
                .body(MyResponse.class);
    }
}
```

Key changes:
- Inject `RestClient restClientTexas` instead of `WebClient`
- `.bodyToMono(T.class).block()` → `.body(T.class)`
- OAuth2 filter function → `.attribute(TARGET_SCOPE, scope)` triggers Texas
- No more `@Qualifier("azureOauth2WebClient")` — just inject the `restClientTexas` bean

## Migrating reactive resilience operators

If the WebClient consumer used reactive resilience4j operators, replace them with annotations.

### Before (reactive operators)

```java
public MyResponse fetchData(String id) {
    return webClient.get()
            .uri("/{id}", id)
            .retrieve()
            .bodyToMono(MyResponse.class)
            .transformDeferred(CircuitBreakerOperator.of(circuitBreaker))
            .transformDeferred(RetryOperator.of(retry))
            .block();
}
```

### After (annotations)

```java
@CircuitBreaker(name = "my-service")
@Retryable(includes = MyTechnicalException.class)
public MyResponse fetchData(String id) {
    return restClient.get()
            .uri("/{id}", id)
            .attribute(NaisTexasRequestInterceptor.TARGET_SCOPE, targetScope)
            .retrieve()
            .body(MyResponse.class);
}
```

The annotations require:
- AOP dependency — either `spring-boot-starter-aop` or `aspectjweaver` directly (the latter is version-managed by the Spring Boot BOM and works when the parent POM doesn't manage `spring-boot-starter-aop`)
- `@EnableResilientMethods` on the application class (for Spring `@Retryable`)
- Verify `spring.aop.auto` is NOT set to `false` in properties

### Aspect ordering note

When combining `@CircuitBreaker` with `@Retryable`:
- Circuit breaker is the **outer** aspect (wraps retry)
- Each method invocation = 1 circuit breaker call, regardless of how many retries happen inside
- This differs from reactive operators where `RetryOperator` wrapping `CircuitBreakerOperator` meant each retry was a separate CB call

## Migrating ExchangeFilterFunction to interceptor

If you had custom `ExchangeFilterFunction` implementations (e.g., for adding headers), migrate them to `ClientHttpRequestInterceptor`.

### Before

```java
public class NavHeadersExchangeFilterFunction implements ExchangeFilterFunction {
    @Override
    public Mono<ClientResponse> filter(ClientRequest request, ExchangeFunction next) {
        return next.exchange(ClientRequest.from(request)
                .header("Nav-Callid", MDC.get("callId"))
                .build());
    }
}
```

### After

Custom Nav-CallId headers are no longer needed — distributed tracing is handled by OpenTelemetry on the NAIS platform. Simply remove the `ExchangeFilterFunction` without replacement.

If you have custom headers **other than** call-id/correlation-id, convert them to `ClientHttpRequestInterceptor` or use `defaultHeaders` on the RestClient builder.

## WebClient with `.exchangeToMono()` patterns

If your WebClient code used `.exchangeToMono()` for fine-grained status handling:

### Before

```java
return webClient.get()
        .uri("/{id}", id)
        .exchangeToMono(response -> {
            if (response.statusCode().is2xxSuccessful()) {
                return response.bodyToMono(MyResponse.class);
            } else if (response.statusCode() == HttpStatus.NOT_FOUND) {
                return Mono.empty();
            } else {
                return response.createException().flatMap(Mono::error);
            }
        })
        .block();
```

### After

```java
return restClient.get()
        .uri("/{id}", id)
        .exchange((_, res) -> {
            if (res.getStatusCode().is2xxSuccessful()) {
                return res.bodyTo(MyResponse.class);
            } else if (NOT_FOUND.isSameCodeAs(res.getStatusCode())) {
                return null;
            } else {
                handleError(res);
                return null; // unreachable — handleError throws
            }
        });
```

## Common gotchas

1. **Don't forget `.block()` removal** — WebClient returns `Mono<T>`, so you probably had `.block()` at the end. RestClient returns `T` directly — no `.block()` needed.

2. **`ExchangeFilterFunction` won't work** — RestClient uses `ClientHttpRequestInterceptor`, not reactive filter functions. If your WebClient builder added filters, you need to convert them to interceptors.

3. **Error types change** — `WebClientResponseException` → `HttpClientErrorException` / `HttpServerErrorException` (or use `defaultStatusHandler` to throw your own exceptions — see `error-handling.md`).

4. **Reactive dependencies may become unused** — After migration, check if `spring-boot-starter-webclient`, `resilience4j-reactor`, and `reactor-core` are still needed. If this was the last reactive code, remove them.

5. **Reactor context propagation code can be removed** — If the app had `ContextRegistry` / `Hooks.enableAutomaticContextPropagation()` setup (typically in an `ApplicationStartedEventListener` or similar) for propagating MDC context through reactive chains, this is no longer needed after migrating away from WebClient. Remove the listener, any `spring.factories` / `AutoConfiguration.imports` entry that registers it, and the `io.micrometer:context-propagation` dependency.
