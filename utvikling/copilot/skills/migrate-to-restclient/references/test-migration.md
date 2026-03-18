# Test Migration

Guide for updating tests when migrating from WebClient/RestTemplate to RestClient.

## Stubbing Texas tokens with WireMock

Replace old OAuth2/Maskinporten token stubs with a single Texas stub.

### Before (separate stubs for Azure and Maskinporten)

```java
protected void stubAzure() {
    stubFor(post(urlEqualTo("/oauth2/v2.0/token"))
            .willReturn(okJson("{\"access_token\":\"mock-azure-token\",\"token_type\":\"Bearer\",\"expires_in\":3600}")));
}

protected void stubMaskinporten() {
    stubFor(post(urlEqualTo("/maskinporten/token"))
            .willReturn(okJson("{\"access_token\":\"mock-maskinporten-token\",\"token_type\":\"Bearer\",\"expires_in\":3600}")));
}
```

### After (single Texas stub)

```java
protected void stubTexas() {
    stubFor(post(urlPathEqualTo("/nais-texas"))
            .willReturn(aResponse()
                    .withStatus(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("{\"access_token\":\"dummy-texas-token\",\"token_type\":\"Bearer\",\"expires_in\":3600}")));
}
```

This single stub handles both Entra ID and Maskinporten token requests since they go to the same Texas endpoint (just with different `identity_provider` form parameters).

### Test properties

```properties
# application-itest.properties (or application-test.properties)

# Texas endpoint → WireMock
nais.token-endpoint=http://localhost:${wiremock.server.port}/nais-texas

# Remove old auth properties:
# azure.app.client-id=...
# azure.app.client-secret=...
# azure.openid-config.token-endpoint=...
# maskinporten.jwt.token-endpoint=...
# keystore.path=...
```

## WebTestClient → RestTestClient

Spring Boot 4 introduced `RestTestClient` as the synchronous counterpart to `WebTestClient`. If you're already on Spring Boot 4, consider migrating.

### Before (WebTestClient)

```java
@AutoConfigureWebTestClient
public abstract class AbstractIT {

    @Autowired
    public WebTestClient webTestClient;

    // ...
}

// In test
webTestClient.post()
        .uri("/api/endpoint")
        .contentType(MediaType.APPLICATION_JSON)
        .bodyValue(requestBody)
        .exchange()
        .expectStatus().isOk()
        .expectBody(MyResponse.class)
        .returnResult()
        .getResponseBody();
```

### After (RestTestClient)

```java
@AutoConfigureRestTestClient
public abstract class AbstractIT {

    @Autowired
    public RestTestClient restTestClient;

    // ...
}

// In test — API is nearly identical
restTestClient.post()
        .uri("/api/endpoint")
        .contentType(MediaType.APPLICATION_JSON)
        .bodyValue(requestBody)
        .exchange()
        .expectStatus().isOk()
        .expectBody(MyResponse.class)
        .returnResult()
        .getResponseBody();
```

The API is almost identical — most changes are mechanical find-and-replace.

### RestTestClient binding modes

- **`.bindToServer()`** — binds to the actual running server. Use this when your tests need interceptors, token-support `@Protected` annotations, or other server-side behavior to be evaluated. This is what `@AutoConfigureRestTestClient` uses with `@SpringBootTest(webEnvironment = RANDOM_PORT)`.

- **`.bindToController(MyController.class)`** — creates a lightweight test that doesn't start the full server. Faster and uses fewer resources, but interceptors and filters don't run.

### Test dependency

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-resttestclient</artifactId>
    <scope>test</scope>
</dependency>
```

Note: On Spring Boot 4, the import is:
```java
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureRestTestClient;
import org.springframework.test.web.servlet.client.RestTestClient;
```

## Cleaning up old test infrastructure

After migration, remove:

1. **`RestTemplateTestConfig.java`** — if you had a test config providing a `RestTemplate` bean, it's no longer needed
2. **`@AutoConfigureWebTestClient`** → `@AutoConfigureRestTestClient`
3. **Old token stubs** — `stubAzure()`, `stubMaskinporten()` → `stubTexas()`
4. **RestTemplate autowiring** in test base classes

## Test dependency changes

### Remove (if no longer needed)

```xml
<!-- Only if no test code uses WebTestClient anymore -->
<dependency>spring-boot-webtestclient</dependency>
<dependency>spring-boot-starter-webclient-test</dependency>
```

### Add

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-resttestclient</artifactId>
    <scope>test</scope>
</dependency>
```

## Example: Complete test base class

```java
@SpringBootTest(
        classes = {ApplicationTestConfig.class},
        webEnvironment = RANDOM_PORT
)
@EnableWireMock
@ActiveProfiles("itest")
@AutoConfigureRestTestClient
@DirtiesContext
public abstract class AbstractIT {

    @Autowired
    public RestTestClient restTestClient;

    @Autowired
    protected CircuitBreakerRegistry circuitBreakerRegistry;

    protected void resetCircuitBreakers() {
        circuitBreakerRegistry.getAllCircuitBreakers().forEach(CircuitBreaker::reset);
    }

    protected void stubTexas() {
        stubFor(post(urlPathEqualTo("/nais-texas"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody("{\"access_token\":\"dummy-texas-token\",\"token_type\":\"Bearer\",\"expires_in\":3600}")));
    }

    // ... other stubs for downstream services
}
```
