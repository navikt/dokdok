# Error Handling Patterns

All consumers should use a private `handleError` method to centralize error handling logic. The `defaultStatusHandler` on the builder simply delegates to this method, keeping the builder lean and the error logic in one readable place.

## Standard pattern: `defaultStatusHandler` + private `handleError`

### Setup (in constructor)

```java
private static final String SERVICE_NAME = "my-service";

public MyConsumer(RestClient restClientTexas, AppProperties props) {
    this.restClient = restClientTexas.mutate()
            .baseUrl(props.getMyService().getUrl())
            .defaultHeader(CONTENT_TYPE, APPLICATION_JSON_VALUE)
            .defaultStatusHandler(HttpStatusCode::isError, (_, res) -> handleError(res))
            .build();
}
```

### The `handleError` method

Every consumer gets a private `handleError` method that reads the response body, logs a warning, and throws the appropriate exception:

```java
private void handleError(ClientHttpResponse response) throws IOException {
    String body = new String(response.getBody().readAllBytes(), StandardCharsets.UTF_8);
    String feilmelding = "Kall mot %s feilet %s med status=%s, body=%s"
            .formatted(SERVICE_NAME,
                    response.getStatusCode().is4xxClientError() ? "funksjonelt" : "teknisk",
                    response.getStatusCode(), body);
    log.warn(feilmelding);
    if (response.getStatusCode().is4xxClientError()) {
        throw new MyFunctionalException(feilmelding, null);
    }
    throw new MyTechnicalException(feilmelding, null);
}
```

### Usage (clean method bodies)

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

The method body is pure business logic — no error handling code. The `defaultStatusHandler` delegates to `handleError`, which intercepts any error responses and throws the appropriate exception before `.body()` is called.

### Why this pattern works well

- **Single responsibility**: Error logic lives in one method, easy to read and maintain
- **Clean builder**: Just one line — `defaultStatusHandler(HttpStatusCode::isError, (_, res) -> handleError(res))`
- **Retry-friendly**: Throwing `TechnicalException` on 5xx means `@Retryable(includes = TechnicalException.class)` will retry server errors but not client errors
- **Consistent**: All methods on the same RestClient instance get the same error handling

## Variation: `.exchange()` for conditional returns

Use `.exchange()` when the consumer needs to inspect the HTTP status and return something other than an exception — typically `null` on 404 ("not found"). The same `handleError` method is reused for non-special status codes.

### Example: null on 404

```java
public EnhetResponse hentEnhet(String orgnr) {
    return restClient.get()
            .uri("/enheter/{orgnr}", orgnr)
            .exchange((_, res) -> {
                if (res.getStatusCode().isError()) {
                    if (NOT_FOUND.isSameCodeAs(res.getStatusCode())) {
                        log.warn("Enhet med orgnr={} ikke funnet", orgnr);
                        return null;
                    }
                    handleError(res);
                }
                return res.bodyTo(EnhetResponse.class);
            });
}
```

The `handleError` method is the same one used by `defaultStatusHandler` — no duplication needed.

### Important: `.exchange()` disables `defaultStatusHandler`

When you use `.exchange()`, the `defaultStatusHandler` configured on the builder does **not** apply for that request. The `.exchange()` callback gets the raw response and you handle all status codes yourself. This is by design — `.exchange()` gives you full control.

This means consumers that use `.exchange()` for some methods and `.retrieve()` for others need to be careful: `.retrieve()` methods will use the `defaultStatusHandler`, but `.exchange()` methods won't. Both paths should call the same `handleError` method so the behavior stays consistent.

## Consistent error message format

Regardless of which pattern you use, standardize the error message format across all consumers:

```
Kall mot {service-name} feilet {funksjonelt|teknisk} med status={status-code}, body={response-body}
```

This makes log searching and alerting consistent. "Funksjonelt" (functional) = client did something wrong (4xx). "Teknisk" (technical) = server error (5xx), worth retrying.

## Exception hierarchy

A typical pattern for NAV apps:

```
RuntimeException
├── AppFunctionalException (base for 4xx errors)
│   ├── ServiceAFunctionalException
│   └── ServiceBFunctionalException
└── AppTechnicalException (base for 5xx errors)
    ├── ServiceATechnicalException
    └── ServiceBTechnicalException
```

Using a common base `TechnicalException` makes `@Retryable(includes = AppTechnicalException.class)` work across all consumers — retry on any server error, never on client errors.

## Choosing between the patterns

| Scenario | Pattern | Reason |
|----------|---------|--------|
| Always throw on errors | `defaultStatusHandler` | Cleanest — error handling in builder, methods stay fluent |
| Return null on 404 | `.exchange()` | Need to inspect status before deciding what to return |
| Different behavior per method | `.exchange()` for special methods, `defaultStatusHandler` for the rest | Mix both on the same RestClient |
| Parse error response body into typed object | `.exchange()` | Need full control over response parsing |
