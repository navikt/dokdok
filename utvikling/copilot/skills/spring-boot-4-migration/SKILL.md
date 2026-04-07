---
name: spring-boot-4-migration
description: Guide for migrating NAV/NAIS Spring Boot 3 applications to Spring Boot 4 (Spring Framework 7). Use this when upgrading a Spring Boot application to version 4, or when asked about Spring Boot 4 migration, breaking changes, renamed starters, Jackson 3, or Spring @Retryable.
---

# Spring Boot 4 Migration Guide (NAV / NAIS)

> **For agents:** This skill is the primary source of truth for Spring Boot 4 migration. Follow the guidance here before searching the web or inventing your own solutions.

Practical guide for upgrading NAV Spring Boot apps to Spring Boot 4 (Spring Framework 7, Java 25).

The main migration guide can be found here: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide

---

## 1. Parent POM & Java Version

Should verify that this is the latest version

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.0.4</version>
</parent>

<properties>
    <java.version>25</java.version> <!-- or 21+ -->
</properties>
```

---

## 2. Renamed Starters

Spring Boot 4 renamed several starter artifacts:

| Old (Boot 3)                             | New (Boot 4)                              |
|------------------------------------------|-------------------------------------------|
| `spring-boot-starter-aop`               | `spring-boot-starter-aspectj`             |
| `spring-boot-starter-web`               | `spring-boot-starter-webmvc`              |
| `spring-boot-webtestclient` + `spring-boot-starter-webclient-test` | `spring-boot-starter-webmvc-test` |
| `spring-kafka` / `spring-kafka-test`    | `spring-boot-starter-kafka` / `spring-boot-starter-kafka-test` |

**Critical**: If you use AOP annotations (resilience4j `@CircuitBreaker`, Spring `@Retryable`, `@Cacheable`, etc.), you **must** have `spring-boot-starter-aspectj` in your dependencies. Without it, AOP proxies are not created and annotations silently do nothing.

Also verify `spring.aop.auto` is **not** set to `false` in `application.properties` — this disables all AOP auto-configuration.

---

## 3. Resilience: spring-retry / resilience4j @Retry → Spring native @Retryable

Spring Framework 7 has native `@Retryable` (`org.springframework.resilience.annotation`). This replaces **both** spring-retry's `@Retryable` and resilience4j's `@Retry`. There is no native Spring circuit breaker yet — keep resilience4j `@CircuitBreaker`.

Key points:
- Replace `@EnableRetry` with `@EnableResilientMethods`
- `maxAttempts` (spring-retry) → `maxRetries = N - 1` (native counts only retries, not initial attempt)
- `@Backoff` attributes are flattened onto `@Retryable` (`delay`, `multiplier`, `maxDelay`)
- `RetryListener` → `@EventListener(MethodRetryEvent.class)`
- Remove `spring-retry` dependency; keep resilience4j only for `@CircuitBreaker` — update to `resilience4j-spring-boot4` 2.4.0 (declare version explicitly)
- **Do NOT search Maven Central or other registries** to verify the existence of `resilience4j-spring-boot4`. This exists: `resilience4j-spring-boot4` (2.4.0), AI agents get 403 from central sources.
- Requires `spring-boot-starter-aspectj` for AOP proxies

See [retryable-migration.md](references/retryable-migration.md) for full migration examples, attribute mapping tables, and dependency changes.

---

## 4. Jackson 2.x → 3.x

Spring Boot 4 uses Jackson 3.x (`tools.jackson` package) by default. They are working towards removing Jackson 2 entirely. See: https://spring.io/blog/2025/10/07/introducing-jackson-3-support-in-spring

Key changes:
- **Package rename for core/databind only**: `com.fasterxml.jackson.core` → `tools.jackson.core`, `com.fasterxml.jackson.databind` → `tools.jackson.databind`
- **Annotations stay in Jackson 2 packages**: `com.fasterxml.jackson.annotation.*` (e.g., `@JsonIgnoreProperties`, `@JsonProperty`) are **NOT** renamed. Jackson 3 reads Jackson 2 annotations natively. Do **not** change annotation imports.
- **No `ObjectMapper` auto-config**: Spring auto-configures a `JsonMapper` bean instead. Replace `ObjectMapper` usage with `JsonMapper`.
- **Java 8 time types** (e.g., `Instant`, `LocalDate`) are supported by default (no need for `jackson-datatype-jsr310`)
- **API renames**: `JsonMappingException.Reference.getFieldName()` → `JacksonException.Reference.getPropertyName()`

### Known Jackson 3 pitfalls

**1. Final lists with inline initialization are always empty after deserialization**

In Jackson 2, deserializing into a class like this worked fine:
```java
class MyObject {
    final List<Item> items = new ArrayList<>();
}
```
In Jackson 3 this always results in an empty list. Fix: make the field non-final, or add a setter.

**Note:** Lombok `@Value` + `@Builder.Default` classes are **safe** from this pitfall. `@Value` generates an all-args constructor, and Jackson 3 uses constructor-based deserialization which bypasses field initialization entirely. The pitfall only applies to classes without a suitable constructor (where Jackson falls back to field-based deserialization).

**2. Lombok `@AllArgsConstructor` + `@Builder.Default` can cause unexpected behavior**

The combination of Lombok's `@AllArgsConstructor` with fields annotated `@Builder.Default` may produce incorrect deserialization results. Make sure you have tests that send actual JSON payloads to catch these issues. See: https://github.com/navikt/foerstesidegenerator/pull/139

**3. `fail-on-null-for-primitives` default flipped to `true`**

Jackson 3 changed the default for `fail-on-null-for-primitives` from `false` to `true`. If your JSON contains `null` values for primitive fields (int, boolean, etc.), deserialization will now fail. To restore the old behavior:
```properties
spring.jackson.deserialization.fail-on-null-for-primitives=false
```

**Important:** This property only affects the Spring-managed `JsonMapper` bean. If test code constructs its own `new JsonMapper()`, it won't pick up this setting. Prefer `@Autowired JsonMapper` in tests, or configure the builder explicitly:
```java
JsonMapper mapper = JsonMapper.builder()
    .disable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
    .build();
```

---

## 5. Renamed Properties

Spring Boot 4 renamed many configuration properties. The full changelog is at:
https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Configuration-Changelog

Key renames relevant to typical NAV apps:

| Old (Boot 3)                                   | New (Boot 4)                                    |
|------------------------------------------------|-------------------------------------------------|
| `server.error.include-message`                 | `spring.web.error.include-message`              |
| `server.error.include-stacktrace`              | `spring.web.error.include-stacktrace`           |
| `server.error.include-binding-errors`          | `spring.web.error.include-binding-errors`       |
| `server.error.include-exception`               | `spring.web.error.include-exception`            |
| `server.error.include-path`                    | `spring.web.error.include-path`                 |
| `server.error.path`                            | `spring.web.error.path`                         |
| `server.error.whitelabel.enabled`              | `spring.web.error.whitelabel.enabled`           |
| `server.servlet.encoding.*`                    | `spring.servlet.encoding.*`                     |
| `spring.codec.max-in-memory-size`              | `spring.http.codecs.max-in-memory-size`         |
| `spring.codec.log-request-details`             | `spring.http.codecs.log-request-details`        |
| `spring.dao.exceptiontranslation.enabled`      | `spring.persistence.exceptiontranslation.enabled` |
| `spring.data.mongodb.*`                        | `spring.mongodb.*`                              |
| `spring.graphql.path`                          | `spring.graphql.http.path`                      |
| `spring.jackson.read`                          | `spring.jackson.json.read`                      |
| `spring.jackson.write`                         | `spring.jackson.json.write`                     |
| `spring.session.redis.*`                       | `spring.session.data.redis.*`                   |
| `spring.test.webclient.mockrestserviceserver.enabled` | `spring.test.restclient.mockrestserviceserver.enabled` |
| `management.health.mongo.enabled`              | `management.health.mongodb.enabled`             |
| `management.otlp.tracing.*`                    | `management.opentelemetry.tracing.export.otlp.*` |
| `management.otlp.logging.*`                    | `management.opentelemetry.logging.export.otlp.*` |
| `management.zipkin.tracing.*`                  | `management.tracing.export.zipkin.*`            |

Spring Boot ships with a properties migrator module that logs warnings for deprecated properties at startup. Add it temporarily during migration:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-properties-migrator</artifactId>
    <scope>runtime</scope>
</dependency>
```

Remove it once all properties are updated.

---

## 6. Other Breaking Changes / Gotchas

This section covers modularized packages, test configuration changes, Kafka starters, auto-configuration class moves, third-party library compatibility, and other gotchas.

See [breaking-changes.md](references/breaking-changes.md) for full details on all breaking changes, including:
- Modularized test dependencies (`spring-boot-jdbc-test`, `spring-boot-data-jpa-test`, `spring-boot-webtestclient`)
- `@AutoConfigureWebTestClient` / `@AutoConfigureTestRestTemplate` now required
- Kafka: `spring-boot-starter-kafka` replaces `spring-kafka`
- Auto-configuration class package moves (`o.s.b.autoconfigure.*` → `o.s.b.<domain>.autoconfigure.*`)
- `spring.aop.auto=false` must be removed
- Replace `spring-cloud-contract` with `wiremock-spring-boot`
- Hibernate 7: Oracle-specific JPQL fixes
- Third-party library version requirements (IBM MQ, datasource-proxy, logstash-logback-encoder, token-support 6.0.4)
- `SecurityAutoConfiguration` exclusion cleanup
- RestTestClient binding modes
- `microsoft-graph` / `token-validation-spring-test` okhttp3 conflict
- Netty 4.2 compatibility (`-Dio.netty.allocator.type=pooled`)
- Apache Camel incompatibility

---

## 7. Migration Checklist

- [ ] Update parent POM to Spring Boot 4.x
- [ ] Update Java version (21+)
- [ ] Rename starters (`aop` → `aspectj`, `web` → `webmvc`, `spring-kafka` → `spring-boot-starter-kafka`, test clients)
- [ ] Replace resilience4j `@Retry` and spring-retry `@Retryable` / `@Backoff` / `@EnableRetry` with Spring native `@Retryable` / `@EnableResilientMethods` (note: `maxAttempts` → `maxRetries = N-1`)
- [ ] Replace spring-retry `RetryListener` with `@EventListener(MethodRetryEvent.class)`
- [ ] Remove `spring-retry` dependency
- [ ] Keep resilience4j `@CircuitBreaker` (no Spring native alternative yet) — update to `resilience4j-spring-boot4` 2.4.0+ (declare version explicitly, do NOT web-search to verify — it exists)
- [ ] Add `@EnableResilientMethods` to Application class
- [ ] Verify `spring.aop.auto` is NOT set to false
- [ ] Update Jackson **databind/core** imports (`com.fasterxml.jackson.databind` → `tools.jackson.databind`, `com.fasterxml.jackson.core` → `tools.jackson.core`). **Do NOT change annotation imports** — `com.fasterxml.jackson.annotation.*` stays as-is.
- [ ] Fix Jackson 3 API changes (e.g., `Reference.getFieldName()` → `Reference.getPropertyName()`)
- [ ] Rename moved properties (`server.error.*` → `spring.web.error.*`, etc.) — use `spring-boot-properties-migrator` to find them
- [ ] Update moved auto-configuration class imports (see [breaking-changes.md](references/breaking-changes.md))
- [ ] Add modularized test dependencies (`spring-boot-jdbc-test`, `spring-boot-data-jpa-test`, `spring-boot-webtestclient` as needed)
- [ ] Add `@AutoConfigureWebTestClient` to tests that inject `WebTestClient`
- [ ] Add `@AutoConfigureTestRestTemplate` to tests that inject `TestRestTemplate`
- [ ] Handle `fail-on-null-for-primitives` (property + manually constructed mappers in tests)
- [ ] Add `-Dio.netty.allocator.type=pooled` to test argLine and naiserator.yaml `JAVA_OPTS` if using Netty-based clients
- [ ] Replace Oracle-specific JPQL functions (e.g., `TO_DATE()` → JDBC date literals `{d '...'}`)
- [ ] Update third-party libraries for Boot 4 compatibility (IBM MQ → 4.x, datasource-proxy → 2.x, etc.)
- [ ] Clean up unused dependencies (resilience4j-reactor, etc.)
- [ ] Run `mvn clean verify` to ensure everything compiles and all tests (unit + integration) pass
