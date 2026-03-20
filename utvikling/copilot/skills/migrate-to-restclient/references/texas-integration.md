# Texas Token Exchange Integration

TEXAS (Token Exchange As a Service) is a NAIS platform sidecar that handles token acquisition for both Entra ID and Maskinporten. Instead of your app managing OAuth2 clients, JWT signing, or certificate-based auth, you POST to a local endpoint and get back a bearer token.

Docs: https://docs.nais.io/auth/explanations/?h=texas#texas

## Architecture

```
Consumer (e.g., PdlConsumer)
    → sets .attribute(TARGET_SCOPE, "api://cluster.namespace.app/.default")
    → RestClient with interceptor
        → NaisTexasRequestInterceptor (ClientHttpRequestInterceptor)
            → detects TARGET_SCOPE or MASKINPORTEN_SCOPE attribute
            → calls NaisTexasConsumer to fetch token from Texas sidecar
            → sets Authorization: Bearer <token>
        → request proceeds to target service
```

## Setup — 4 files + config

### 1. NaisProperties.java — Config binding (package: `config.nais`)

```java
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@ConfigurationProperties("nais")
@Validated
public record NaisProperties(@NotBlank String tokenEndpoint) {
}
```

Register it with `@EnableConfigurationProperties(NaisProperties.class)` on your application or config class.

### 2. NaisTexasToken.java — Response DTO (package: `consumer.nais`)

```java
import com.fasterxml.jackson.annotation.JsonProperty;

record NaisTexasToken(@JsonProperty("access_token") String accessToken) {
}
```

Note: If you're on Jackson 3 (Spring Boot 4), the annotation package changes to `tools.jackson.annotation.JsonProperty`.

### 3. NaisTexasConsumer.java — Token retrieval (package: `consumer.nais`)

Handles both Entra ID and Maskinporten tokens via the same Texas endpoint. Uses `Optional` to safely handle null responses — this catches both a null response body and a null `accessToken` field, throwing a descriptive exception rather than NPE.

```java
import lombok.extern.slf4j.Slf4j;
import no.nav.myapp.config.nais.NaisProperties;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Optional;

import static java.lang.String.join;
import static org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED;

@Slf4j
@Component
public class NaisTexasConsumer {

    private final RestClient restClient;

    public NaisTexasConsumer(RestClient.Builder restClientBuilder, NaisProperties naisProperties) {
        this.restClient = restClientBuilder
                .baseUrl(naisProperties.tokenEndpoint())
                .defaultStatusHandler(HttpStatusCode::isError, (_, res) -> handleError(res))
                .build();
    }

    public String getSystemToken(String targetScope) {
        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("identity_provider", "azuread");
        formData.add("target", targetScope);

        return Optional.ofNullable(restClient.post()
                .contentType(APPLICATION_FORM_URLENCODED)
                .body(formData)
                .retrieve()
                .body(NaisTexasToken.class))
                .map(NaisTexasToken::accessToken)
                .orElseThrow(() -> new RuntimeException("Tomt token-svar fra NAIS Texas (azuread)"));
    }

    public String getMaskinportenToken(String... targetScopes) {
        String formattedScopes = join(" ", targetScopes);

        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("identity_provider", "maskinporten");
        formData.add("target", formattedScopes);

        return Optional.ofNullable(restClient.post()
                .contentType(APPLICATION_FORM_URLENCODED)
                .body(formData)
                .retrieve()
                .body(NaisTexasToken.class))
                .map(NaisTexasToken::accessToken)
                .orElseThrow(() -> new RuntimeException("Tomt token-svar fra NAIS Texas (maskinporten)"));
    }

    private void handleError(ClientHttpResponse response) throws IOException {
        String body = new String(response.getBody().readAllBytes(), StandardCharsets.UTF_8);
        String feilmelding = "Tokenforespørsel til NAIS Texas feilet med status=%s, body=%s"
                .formatted(response.getStatusCode(), body);
        log.error(feilmelding);
        throw new RuntimeException(feilmelding);
    }
}
```

### 4. NaisTexasRequestInterceptor.java — Auto-injects tokens (package: `consumer.nais`)

The interceptor checks for request attributes to decide which token type to fetch. Consumers set the attribute, and the interceptor handles the rest.

```java
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;

import java.io.IOException;
import java.util.Map;

public class NaisTexasRequestInterceptor implements ClientHttpRequestInterceptor {

    public static final String TARGET_SCOPE = "targetScope";
    public static final String MASKINPORTEN_SCOPE = "maskinportenScope";

    private final NaisTexasConsumer naisTexasConsumer;

    public NaisTexasRequestInterceptor(NaisTexasConsumer naisTexasConsumer) {
        this.naisTexasConsumer = naisTexasConsumer;
    }

    @Override
    public ClientHttpResponse intercept(HttpRequest request, byte[] body,
                                         ClientHttpRequestExecution execution) throws IOException {
        Map<String, Object> attributes = request.getAttributes();

        if (attributes.containsKey(TARGET_SCOPE)) {
            String targetScope = (String) attributes.get(TARGET_SCOPE);
            request.getHeaders().setBearerAuth(naisTexasConsumer.getSystemToken(targetScope));
        } else if (attributes.containsKey(MASKINPORTEN_SCOPE)) {
            String maskinportenScope = (String) attributes.get(MASKINPORTEN_SCOPE);
            request.getHeaders().setBearerAuth(naisTexasConsumer.getMaskinportenToken(maskinportenScope));
        }

        return execution.execute(request, body);
    }
}
```

### 5. RestClientConfig.java — Wires it together (package: `config.nais`)

```java
import no.nav.myapp.consumer.nais.NaisTexasConsumer;
import no.nav.myapp.consumer.nais.NaisTexasRequestInterceptor;
import org.springframework.boot.http.client.ClientHttpRequestFactoryBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Configuration
public class RestClientConfig {

    @Bean
    RestClient restClientTexas(RestClient.Builder restClientBuilder, NaisTexasConsumer naisTexasConsumer) {
        return restClientBuilder
                .requestFactory(jdkClientHttpRequestFactory())
                .requestInterceptor(new NaisTexasRequestInterceptor(naisTexasConsumer))
                .build();
    }

    private static JdkClientHttpRequestFactory jdkClientHttpRequestFactory() {
        return ClientHttpRequestFactoryBuilder.jdk()
                .withCustomizer(factory -> factory.setReadTimeout(Duration.ofSeconds(20)))
                .build();
    }
}
```

## Configuration

```properties
# Production — NAIS injects NAIS_TOKEN_ENDPOINT automatically:
nais.token-endpoint=${NAIS_TOKEN_ENDPOINT}

# Test — point to WireMock:
nais.token-endpoint=http://localhost:${wiremock.server.port}/nais-texas
```

## Usage in consumers

### Entra ID consumer

```java
@Component
public class PdlConsumer {
    private final RestClient restClient;
    private final String targetScope;

    public PdlConsumer(RestClient restClientTexas, AppProperties props) {
        this.restClient = restClientTexas.mutate()
                .baseUrl(props.getPdl().getUrl())
                .build();
        this.targetScope = props.getPdl().getScope();
    }

    public PersonResponse hentPerson(String ident) {
        return restClient.post()
                .attribute(NaisTexasRequestInterceptor.TARGET_SCOPE, targetScope)
                .body(buildRequest(ident))
                .retrieve()
                .body(PersonResponse.class);
    }
}
```

### Maskinporten consumer

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
                .uri(uriBuilder -> uriBuilder.path("/validate").queryParam("orgNr", orgnr).build())
                .attributes(attrs -> attrs.put(NaisTexasRequestInterceptor.MASKINPORTEN_SCOPE, maskinportenScope))
                .retrieve()
                .body(ValidateResponse.class);
    }
}
```

### No-auth consumer

Consumers without authentication still benefit from the shared RestClient for consistent timeout configuration:

```java
@Component
public class BrregConsumer {
    private final RestClient restClient;

    public BrregConsumer(RestClient restClientTexas, AppProperties props) {
        this.restClient = restClientTexas.mutate()
                .baseUrl(props.getBrreg().getUrl())
                .build();
    }

    public EnhetResponse hentEnhet(String orgnr) {
        return restClient.get()
                .uri("/enheter/{orgnr}", orgnr)
                .retrieve()
                .body(EnhetResponse.class);
    }
}
```

## Known limitation: Not all Maskinporten scopes are supported by NAIS Texas

Some Maskinporten scopes — notably `move/dpo.read` used by Digdir's Service Registry (eFormidling) — are **not supported** by the NAIS Maskinporten integration. These scopes require the old certificate-based JWT signing flow with a virksomhetssertifikat.

For consumers that need an unsupported scope, you must keep the manual Maskinporten token flow:
- Retain the `MaskinportenConsumer` (or equivalent) that signs JWTs using `AppCertificate` and `nimbus-jose-jwt`
- Retain `KeyStoreProperties` and the virksomhetssertifikat vault mount in `naiserator.yaml`
- Inject `MaskinportenConsumer` into the affected consumer and set `Bearer` auth directly in the request headers
- The consumer can still use the shared `restClientTexas` bean — just don't set the `MASKINPORTEN_SCOPE` attribute

Example:

```java
@Component
public class ServiceRegistryConsumer {
    private final RestClient restClient;
    private final MaskinportenConsumer maskinportenConsumer;

    public ServiceRegistryConsumer(RestClient restClientTexas,
                                   AppProperties props,
                                   MaskinportenConsumer maskinportenConsumer) {
        this.restClient = restClientTexas.mutate()
                .baseUrl(props.getServiceRegistry().getUrl())
                .build();
        this.maskinportenConsumer = maskinportenConsumer;
    }

    public SomeResponse fetch(String id) {
        return restClient.get()
                .uri("/resource/{id}", id)
                .headers(h -> h.setBearerAuth(maskinportenConsumer.getMaskinportenToken()))
                .retrieve()
                .body(SomeResponse.class);
    }
}
```

## What Texas replaces

| Old pattern | Replaced by |
|-------------|-------------|
| `spring-security-oauth2-client` + reactive `ServerOAuth2AuthorizedClientExchangeFilterFunction` | Texas `TARGET_SCOPE` attribute |
| Manual `MaskinportenConsumer` (JWT signing + certificate) | Texas `MASKINPORTEN_SCOPE` attribute **if scope is supported by NAIS** — otherwise keep old flow (see limitation above) |
| `AzureProperties` / client-id / client-secret config | NAIS env vars (auto-injected by Entra ID integration) |
| Virksomhetssertifikat / keystore files | Not needed for Texas scopes — **still needed** for unsupported scopes (e.g. `move/dpo.read`) |
| `NavHeadersExchangeFilterFunction` (WebClient filter for Nav-CallId) | No longer needed — distributed tracing is handled by OpenTelemetry |

## NAIS configuration

Make sure your `naiserator.yaml` declares the scopes you need:

```yaml
spec:
  azure:
    application:
      enabled: true
  maskinporten:
    enabled: true
    scopes:
      consumes:
        - name: "nav:some/scope"
```
