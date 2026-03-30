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

Spring Framework 7 has native `@Retryable` (`org.springframework.resilience.annotation`). This replaces **both** spring-retry's `@Retryable` and resilience4j's `@Retry`.

**Note**: There is no native Spring circuit breaker yet. Keep resilience4j `@CircuitBreaker` for that.

### Setup

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

### Migrating from spring-retry

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

### Migrating RetryListener

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

### Migrating from resilience4j @Retry

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

### Aspect ordering

When combining resilience4j `@CircuitBreaker` with Spring `@Retryable`:
- Circuit breaker is the **outer** aspect (wraps retry)
- Each method invocation = 1 circuit breaker call, regardless of retries
- This matches the default behavior when both were resilience4j annotations

### Dependencies

```xml
<!-- Remove both -->
<!-- <dependency>org.springframework.retry:spring-retry</dependency> -->
<!-- <dependency>io.github.resilience4j:resilience4j-reactor</dependency> -->

<!-- Keep for @CircuitBreaker -->
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot3</artifactId>
</dependency>
```

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

### Modularized packages — clean up dependencies

Spring Boot 4 split packages and extracted test code into separate modules. You will likely need to clean up dependencies. See: https://spring.io/blog/2025/10/28/modularizing-spring-boot

**Test modules you likely need to add** (these were previously included transitively via `spring-boot-starter-test` but are now separate):

| If you use… | Add dependency |
|---|---|
| `@AutoConfigureTestDatabase` | `spring-boot-jdbc-test` |
| `@DataJpaTest` | `spring-boot-data-jpa-test` |
| `WebTestClient` injection in `@SpringBootTest` | `spring-boot-webtestclient` |
| `RestTestClient` | `spring-boot-resttestclient` |

```xml
<!-- Example: test dependencies for a JPA + WebMvc app -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-jdbc-test</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-data-jpa-test</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-webtestclient</artifactId>
    <scope>test</scope>
</dependency>
```

**Important**: If a module uses test-jars from another module (e.g., `<type>test-jar</type>`), the consuming module must also declare these test dependencies directly — they are not transitively inherited through the test-jar.

### `@AutoConfigureWebTestClient` now required

In Spring Boot 3, `WebTestClient` was auto-configured when using `@SpringBootTest(webEnvironment = RANDOM_PORT)` with webflux on the classpath. In Boot 4, you must explicitly add `@AutoConfigureWebTestClient`:

```java
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;

@SpringBootTest(webEnvironment = RANDOM_PORT)
@AutoConfigureWebTestClient  // Required in Boot 4
public abstract class AbstractITest {
    @Autowired
    public WebTestClient webTestClient;
}
```

### `@AutoConfigureTestRestTemplate` now required

Same as `WebTestClient` above — `TestRestTemplate` is no longer auto-configured. Add `@AutoConfigureTestRestTemplate`:

```java
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;

@SpringBootTest(webEnvironment = RANDOM_PORT)
@AutoConfigureTestRestTemplate  // Required in Boot 4
public abstract class AbstractITest {
    @Autowired
    public TestRestTemplate testRestTemplate;
}
```

### Kafka: use `spring-boot-starter-kafka` instead of `spring-kafka`

Due to modularization, the Kafka auto-configuration (`KafkaAutoConfiguration`, `KafkaTemplate` bean, `ProducerFactory`, `ConsumerFactory`, etc.) has moved out of the monolithic `spring-boot-autoconfigure` into a dedicated `spring-boot-kafka` module. If your app depends on bare `spring-kafka`, the auto-configured beans will **not** be created and you'll get `NoSuchBeanDefinitionException` for `KafkaTemplate` at startup.

**Fix**: Replace direct `spring-kafka` / `spring-kafka-test` dependencies with the new Boot 4 starters:

```xml
<!-- Before (Boot 3) -->
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka-test</artifactId>
    <scope>test</scope>
</dependency>

<!-- After (Boot 4) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-kafka</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-kafka-test</artifactId>
    <scope>test</scope>
</dependency>
```

The new starters transitively pull in `spring-kafka`, `spring-boot-kafka` (which contains the auto-configuration), and `spring-boot-transaction`.

### Auto-configuration class packages moved

The package structure for auto-configuration classes changed from `org.springframework.boot.autoconfigure.<domain>...` to `org.springframework.boot.<domain>.autoconfigure...`. For example:

```java
// Before
import org.springframework.boot.autoconfigure.web.servlet.WebMvcAutoConfiguration;
import org.springframework.boot.actuate.autoconfigure.observation.web.servlet.WebMvcObservationAutoConfiguration;

// After
import org.springframework.boot.webmvc.autoconfigure.WebMvcAutoConfiguration;
import org.springframework.boot.webmvc.autoconfigure.WebMvcObservationAutoConfiguration;
```

Common import changes (non-exhaustive):

| Old (Boot 3) | New (Boot 4) |
|---|---|
| `org.springframework.boot.autoconfigure.domain.EntityScan` | `org.springframework.boot.persistence.autoconfigure.EntityScan` |
| `org.springframework.boot.autoconfigure.jdbc.DataSourceProperties` | `org.springframework.boot.jdbc.autoconfigure.DataSourceProperties` |
| `org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration` | `org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration` |
| `org.springframework.boot.autoconfigure.flyway.FlywayAutoConfiguration` | `org.springframework.boot.flyway.autoconfigure.FlywayAutoConfiguration` |
| `org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase` | `org.springframework.boot.jdbc.test.autoconfigure.AutoConfigureTestDatabase` |
| `org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest` | `org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest` |

**Tip**: When you get a `ClassNotFoundException` for a `o.s.b.autoconfigure.*` class, search the Boot 4 jars for it:
```bash
find ~/.m2/repository/org/springframework/boot -path "*/4.0.4/*.jar" | while read jar; do
  jar tf "$jar" | grep "YourClass.class$" && echo "  ^ in: $jar"
done
```

### `spring.aop.auto=false`

If your `application.properties` contains `spring.aop.auto=false`, **remove it**. This disables all AOP auto-configuration, which means `@CircuitBreaker`, `@Retryable`, `@Cacheable`, `@Transactional`, etc. silently stop working.

### Replace `spring-cloud-contract` starters with WireMock

You don't need `spring-cloud-contract` starters — `wiremock-spring-boot` does the job (we typically don't use any other spring-cloud-contract functionality). Use:

```xml
<dependency>
    <groupId>org.wiremock.integrations</groupId>
    <artifactId>wiremock-spring-boot</artifactId>
    <version>4.0.9</version>
    <scope>test</scope>
</dependency>
```

Note: if your code used `wiremock.org.apache.commons.io.IOUtils` (from the shaded WireMock jar), replace it with standard Java:
```java
// Before
import wiremock.org.apache.commons.io.IOUtils;
String content = IOUtils.toString(inputStream, UTF_8);

// After
String content = new String(inputStream.readAllBytes(), UTF_8);
```

Docs: https://wiremock.org/docs/spring-boot/

### Hibernate 7: Fix Oracle-specific JPQL

**Fix Oracle-specific JPQL**: Replace `TO_DATE()` (Oracle function) with standard JDBC date literals:

```java
// Before (Oracle-specific)
@Query("... WHERE dok.opprettetDato >= TO_DATE('2022-01-01', 'yyyy-mm-dd')")

// After (standard JDBC date literal — works on all databases)
@Query("... WHERE dok.opprettetDato >= {d '2022-01-01'}")
```

### Third-party library compatibility

Some third-party libraries need specific versions for Boot 4:

| Library | Boot 3 version | Boot 4 version | Notes |
|---|---|---|---|
| `mq-jms-spring-boot-starter` (IBM MQ) | 3.x | **4.0.2+** | Major version bump for Boot 4 |
| `datasource-proxy-spring-boot-starter` | 1.12.x | **2.0.0+** | 1.x references old auto-config package paths |
| `logstash-logback-encoder` | 8.x | **9.0+** | Uses Jackson 3, compatible with Boot 4 |
| `token-support` (NAV) | 5.x | **6.0.4+** | Major version bump for Boot 4 |

### `SecurityAutoConfiguration` exclusion may be unnecessary

After Spring Boot modularization, `SecurityAutoConfiguration` is no longer included in the web package. It comes in via `spring-boot-starter-security-oauth2-client`, but if you use `spring-security-oauth2-client` directly instead, it won't be on the classpath. In that case, any `exclude = SecurityAutoConfiguration.class` can simply be removed.

### RestTestClient binding modes

If your tests need token-support `@Protected` annotations (or other interceptors) to be evaluated, you must bind `RestTestClient` with `.bindToServer()`. Otherwise, you can use `.bindToController(...)` which runs with significantly fewer resources.

Test dependency:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-resttestclient</artifactId>
    <scope>test</scope>
</dependency>
```

### Conflict between `microsoft-graph` and `token-validation-spring-test`

Apps using `microsoft-graph` (which pulls in okhttp3 v4) together with `token-validation-spring-test` (which transitively brings `mock-oauth2-server` with okhttp3 v5) will get a runtime conflict.

See: https://github.com/microsoftgraph/msgraph-sdk-java-core/issues/1940

Workaround — pin `mock-oauth2-server` to 2.3.0:
```xml
<dependency>
    <groupId>no.nav.security</groupId>
    <artifactId>mock-oauth2-server</artifactId>
    <version>2.3.0</version>
    <scope>test</scope>
</dependency>
```

### Netty 4.2 compatibility

Spring Boot 4 upgrades to Netty 4.2, which changes the default buffer allocator. This can cause hangs/timeouts when Netty 4.1 transitive dependencies are also on the classpath (e.g. from `microsoft-graph` or other libraries). Fix by setting `-Dio.netty.allocator.type=pooled` in **both** tests and runtime:

See: https://netty.io/wiki/netty-4.2-migration-guide.html

```xml
<!-- In maven-failsafe-plugin or maven-surefire-plugin -->
<argLine>-Dio.netty.allocator.type=pooled</argLine>
```

```yaml
# In naiserator.yaml, under spec.env or spec.envFrom
env:
  - name: JAVA_OPTS
    value: "-Dio.netty.allocator.type=pooled"
```

### Apache Camel is not yet compatible

As of Camel 4.17.0, Camel is not compatible with Spring Boot 4. Spring Boot 4 support in camel is expected in camel 4.19.0.

See: https://issues.apache.org/jira/browse/CAMEL-22463

---

## 7. Migration Checklist

- [ ] Update parent POM to Spring Boot 4.x
- [ ] Update Java version (21+)
- [ ] Rename starters (`aop` → `aspectj`, `web` → `webmvc`, `spring-kafka` → `spring-boot-starter-kafka`, test clients)
- [ ] Replace resilience4j `@Retry` and spring-retry `@Retryable` / `@Backoff` / `@EnableRetry` with Spring native `@Retryable` / `@EnableResilientMethods` (note: `maxAttempts` → `maxRetries = N-1`)
- [ ] Replace spring-retry `RetryListener` with `@EventListener(MethodRetryEvent.class)`
- [ ] Remove `spring-retry` dependency
- [ ] Keep resilience4j `@CircuitBreaker` (no Spring native alternative yet)
- [ ] Add `@EnableResilientMethods` to Application class
- [ ] Verify `spring.aop.auto` is NOT set to false
- [ ] Update Jackson **databind/core** imports (`com.fasterxml.jackson.databind` → `tools.jackson.databind`, `com.fasterxml.jackson.core` → `tools.jackson.core`). **Do NOT change annotation imports** — `com.fasterxml.jackson.annotation.*` stays as-is.
- [ ] Fix Jackson 3 API changes (e.g., `Reference.getFieldName()` → `Reference.getPropertyName()`)
- [ ] Rename moved properties (`server.error.*` → `spring.web.error.*`, etc.) — use `spring-boot-properties-migrator` to find them
- [ ] Update moved auto-configuration class imports (see import table in section 6)
- [ ] Add modularized test dependencies (`spring-boot-jdbc-test`, `spring-boot-data-jpa-test`, `spring-boot-webtestclient` as needed)
- [ ] Add `@AutoConfigureWebTestClient` to tests that inject `WebTestClient`
- [ ] Add `@AutoConfigureTestRestTemplate` to tests that inject `TestRestTemplate`
- [ ] Handle `fail-on-null-for-primitives` (property + manually constructed mappers in tests)
- [ ] Add `-Dio.netty.allocator.type=pooled` to test argLine and naiserator.yaml `JAVA_OPTS` if using Netty-based clients
- [ ] Replace Oracle-specific JPQL functions (e.g., `TO_DATE()` → JDBC date literals `{d '...'}`)
- [ ] Update third-party libraries for Boot 4 compatibility (IBM MQ → 4.x, datasource-proxy → 2.x, etc.)
- [ ] Clean up unused dependencies (resilience4j-reactor, etc.)
- [ ] Run `mvn clean verify` to ensure everything compiles and all tests (unit + integration) pass
