# RestTemplate → RestClient Migration

## Key differences

| RestTemplate | RestClient |
|---|---|
| `restTemplate.getForObject(url, T.class)` | `restClient.get().uri(url).retrieve().body(T.class)` |
| `restTemplate.exchange(url, method, entity, T.class)` | `restClient.method(method).uri(url).body(entity).retrieve().body(T.class)` |
| `RestTemplateBuilder` | `RestClient.Builder` or `RestClient.create(restTemplate)` |
| `ClientHttpRequestInterceptor` | Same — `ClientHttpRequestInterceptor` (shared interface) |
| Error via `HttpClientErrorException` / `HttpServerErrorException` | Same — or use `defaultStatusHandler` for custom mapping |

RestClient and RestTemplate share the same interceptor interface, which makes the migration straightforward — interceptors can be reused as-is.

## Basic migration pattern

### Before (RestTemplate)

```java
@Component
public class AltinnConsumer {
    private final RestTemplate restTemplate;

    public AltinnConsumer(RestTemplateBuilder builder, AppProperties props) {
        this.restTemplate = builder
                .rootUri(props.getAltinn().getUrl())
                .additionalInterceptors(new TokenInterceptor())
                .build();
    }

    public ValidateResponse validate(String orgnr) {
        return restTemplate.getForObject(
                "/serviceowner/validate?organizationNumber={orgnr}",
                ValidateResponse.class,
                orgnr);
    }
}
```

### After (RestClient)

```java
@Component
public class AltinnConsumer {
    private final RestClient restClient;
    private final String maskinportenScope;

    public AltinnConsumer(RestClient restClientTexas, AppProperties props) {
        this.restClient = restClientTexas.mutate()
                .baseUrl(props.getAltinn().getUrl())
                .build();
        this.maskinportenScope = props.getAltinn().getMaskinportenScope();
    }

    public ValidateResponse validate(String orgnr) {
        return restClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/serviceowner/validate")
                        .queryParam("organizationNumber", orgnr)
                        .build())
                .attributes(attrs -> attrs.put(
                        NaisTexasRequestInterceptor.MASKINPORTEN_SCOPE, maskinportenScope))
                .retrieve()
                .body(ValidateResponse.class);
    }
}
```

Key changes:
- `RestTemplate` → `RestClient` (inject `restClientTexas` bean, mutate with baseUrl)
- `restTemplate.getForObject(url, T.class, vars)` → fluent `restClient.get().uri(...).retrieve().body(T.class)`
- Token acquisition via custom interceptor → `.attribute(MASKINPORTEN_SCOPE, scope)` triggers Texas
- URI template variables: RestTemplate inline `{var}` → RestClient `UriBuilder` or path variables

## Migrating `.exchange()`

RestTemplate's `exchange()` method (which gives access to the full response) maps to RestClient's `.exchange()`:

### Before

```java
ResponseEntity<MyResponse> response = restTemplate.exchange(
        url,
        HttpMethod.GET,
        new HttpEntity<>(headers),
        MyResponse.class);

if (response.getStatusCode() == HttpStatus.NOT_FOUND) {
    return null;
}
return response.getBody();
```

### After

```java
return restClient.get()
        .uri(url)
        .exchange((_, res) -> {
            if (NOT_FOUND.isSameCodeAs(res.getStatusCode())) {
                return null;
            }
            if (res.getStatusCode().isError()) {
                handleError(res);
            }
            return res.bodyTo(MyResponse.class);
        });
```

## Migrating try-catch error handling

If your RestTemplate code caught `HttpClientErrorException` / `HttpServerErrorException`:

### Before

```java
public MyResponse fetchData(String id) {
    try {
        return restTemplate.getForObject("/api/{id}", MyResponse.class, id);
    } catch (HttpClientErrorException e) {
        throw new MyFunctionalException("Client error: " + e.getStatusCode());
    } catch (HttpServerErrorException e) {
        throw new MyTechnicalException("Server error: " + e.getStatusCode());
    }
}
```

### After (using `defaultStatusHandler` + private `handleError`)

```java
// In constructor — delegate to private handleError method
this.restClient = restClientTexas.mutate()
        .baseUrl(props.getUrl())
        .defaultStatusHandler(HttpStatusCode::isError, (_, res) -> handleError(res))
        .build();

// Private method centralizes error logic
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

// Method body becomes a clean fluent chain — no try-catch needed
public MyResponse fetchData(String id) {
    return restClient.get()
            .uri("/api/{id}", id)
            .retrieve()
            .body(MyResponse.class);
}
```

See `error-handling.md` for a complete guide to error handling patterns.

## Bridging: `RestClient.create(restTemplate)`

If you want to migrate incrementally, you can create a RestClient backed by an existing RestTemplate:

```java
RestClient restClient = RestClient.create(existingRestTemplate);
```

This preserves all the RestTemplate's interceptors, error handlers, and request factory. Useful as a stepping stone, but the goal should be to fully migrate to RestClient configuration.

## Common gotchas

1. **URI template syntax is the same** — `restClient.get().uri("/api/{id}", id)` works just like RestTemplate. You can also use `UriBuilder` for more complex URIs.

2. **Headers** — RestTemplate used `HttpEntity` for headers. RestClient uses `.header()` or `.headers()` directly on the request. Common headers should go on `defaultHeaders` on the builder.

3. **Interceptors carry over** — If your RestTemplate had `ClientHttpRequestInterceptor` implementations, they work with RestClient too. But if you're adopting Texas, you probably don't need the old token interceptors anymore.

4. **`RestTemplateBuilder` in tests** — If tests used `TestRestTemplate` (which wraps RestTemplate), consider migrating to `RestTestClient` instead. See `test-migration.md`.

5. **Error handler difference** — RestTemplate's `ResponseErrorHandler` is different from RestClient's `defaultStatusHandler`. They're not interchangeable, but the migration is straightforward — see the error handling section above.
