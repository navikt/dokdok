---
name: migrate-to-restclient
description: Guide for migrating NAV/NAIS Spring Boot applications from WebClient or RestTemplate to RestClient. Use this when the user wants to replace WebClient with RestClient, replace RestTemplate with RestClient, add NAIS Texas token exchange, set up RestClient error handling, or migrate HTTP client code in a Spring Boot app. Also use when asked about RestClient patterns, Texas integration, or modernizing HTTP consumers in NAV apps.
---

# Migrate to RestClient (NAV / NAIS)

Guide for replacing `WebClient` (reactive) and `RestTemplate` (legacy) with Spring's `RestClient` (synchronous, fluent) in NAV/NAIS applications.

## When to use this skill

- Replacing `WebClient` with `RestClient` (reactive → synchronous)
- Replacing `RestTemplate` with `RestClient` (legacy → modern)
- Adding NAIS Texas token exchange (Entra ID and/or Maskinporten)
- Standardizing error handling across REST consumers
- Migrating tests from `WebTestClient` to `RestTestClient`

## Decision flowchart

Before starting, assess each consumer:

```
For each consumer:
  1. Does it need authentication?
     ├── Entra ID (machine-to-machine) → Texas with TARGET_SCOPE attribute
     ├── Maskinporten → Texas with MASKINPORTEN_SCOPE attribute
     └── None → Plain RestClient (no attribute needed)

  2. How should errors be handled?
     ├── Always throw on error → Use defaultStatusHandler on builder (cleanest)
     └── Need conditional returns (e.g., null on 404) → Use .exchange()

  3. Does it need resilience annotations?
     ├── Circuit breaker → @CircuitBreaker (resilience4j, no Spring native yet)
     ├── Retry → @Retryable (Spring native, org.springframework.resilience.annotation)
     └── Both → Combine them (CB is outer, wraps retry)
```

## Migration steps

### Step 1: Set up Texas infrastructure (if authentication is needed)

If **any** consumer needs Entra ID or Maskinporten tokens, set up the Texas token exchange infrastructure first. This is a one-time setup for the entire app.

Read `references/texas-integration.md` for the complete setup (4 files + config). Place the token consumer, interceptor, and token DTO in a `consumer.nais` package — not `config` (which should only hold configuration value classes). `NaisProperties` and `RestClientConfig` stay in `config.nais`.

**⚠️ Important:** Not all Maskinporten scopes are supported by the NAIS integration — notably `move/dpo.read` (eFormidling/Service Registry). For unsupported scopes, keep the old certificate-based JWT flow. See the "Known limitation" section in `references/texas-integration.md`.

If no consumers need authentication, skip this step — consumers can use a plain `RestClient.Builder` bean.

### Step 2: Migrate each consumer

For each consumer, identify whether it currently uses `WebClient` or `RestTemplate`:

- **WebClient → RestClient**: Read `references/webclient-migration.md`
- **RestTemplate → RestClient**: Read `references/resttemplate-migration.md`

Both reference files contain before/after examples and common gotchas.

### Step 3: Set up error handling

Choose the appropriate error handling pattern for each consumer and apply it consistently:

- **`defaultStatusHandler`** — for consumers that always throw on HTTP errors (most consumers). Error handling moves to the RestClient builder, keeping method bodies pure fluent chains.
- **`.exchange()`** — for consumers that need to inspect the status code and return something other than an exception (e.g., `null` on 404).

Read `references/error-handling.md` for patterns and examples.

### Step 4: Update tests

Migrate test infrastructure to work with RestClient:

- Replace OAuth2/Maskinporten token stubs with Texas stubs
- Consider migrating from `WebTestClient` to `RestTestClient`
- Clean up test dependencies

Read `references/test-migration.md` for details.

### Step 5: Clean up

After all consumers are migrated:

1. **Delete old infrastructure** — `WebClient` config classes, `ExchangeFilterFunction` implementations, OAuth2 client config, reactor context propagation code (e.g. `ApplicationStartedEventListener` with `Hooks.enableAutomaticContextPropagation()`). **Only** delete `MaskinportenConsumer` / certificate code if all Maskinporten scopes are supported by NAIS Texas — if any consumer still needs an unsupported scope (e.g. `move/dpo.read`), keep the manual JWT signing flow.
2. **Remove unused dependencies** from `pom.xml`:
   - `spring-boot-starter-webclient` (unless still needed for `WebTestClient` in tests)
   - `spring-boot-starter-webflux` (if only used for `WebClient`)
   - `spring-security-oauth2-client` (if only used for WebClient OAuth2 flows)
   - `io.micrometer:context-propagation` (if only used for reactor context propagation)
   - `nimbus-jose-jwt` (only if no consumer still needs manual JWT signing)
   - `httpclient5` (Apache HC5, if only used by old RestTemplate)
   - `resilience4j-reactor` (if migrated from reactive resilience operators to annotations)
3. **Remove unused properties** — `azure.*` client properties. Only remove maskinporten/certificate properties if all scopes are on Texas.
4. **Remove certificate/keystore code** — only if no consumer still needs the old Maskinporten flow

## Key patterns summary

| Pattern | When to use | Example |
|---------|-------------|---------|
| `.attribute(TARGET_SCOPE, scope)` | Entra ID M2M auth | `references/texas-integration.md` |
| `.attribute(MASKINPORTEN_SCOPE, scope)` | Maskinporten auth | `references/texas-integration.md` |
| `defaultStatusHandler` on builder | Always throw on error | `references/error-handling.md` |
| `.exchange()` | Conditional returns (null on 404) | `references/error-handling.md` |
| `.mutate().baseUrl(...)` | Per-consumer customization of shared RestClient | All reference files |

## Reference files

| File | Read when... |
|------|-------------|
| `references/texas-integration.md` | Setting up Texas token exchange (Entra ID / Maskinporten) |
| `references/webclient-migration.md` | Migrating a WebClient consumer to RestClient |
| `references/resttemplate-migration.md` | Migrating a RestTemplate consumer to RestClient |
| `references/error-handling.md` | Choosing and implementing error handling patterns |
| `references/test-migration.md` | Updating tests, stubs, and test dependencies |
