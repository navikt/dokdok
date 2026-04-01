# Other Breaking Changes / Gotchas

## Modularized packages — clean up dependencies

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

## `@AutoConfigureWebTestClient` now required

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

## `@AutoConfigureTestRestTemplate` now required

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

## Kafka: use `spring-boot-starter-kafka` instead of `spring-kafka`

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

## Auto-configuration class packages moved

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

## `spring.aop.auto=false`

If your `application.properties` contains `spring.aop.auto=false`, **remove it**. This disables all AOP auto-configuration, which means `@CircuitBreaker`, `@Retryable`, `@Cacheable`, `@Transactional`, etc. silently stop working.

## Replace `spring-cloud-contract` starters with WireMock

You don't need `spring-cloud-contract` starters — `wiremock-spring-boot` does the job (we typically don't use any other spring-cloud-contract functionality). Use:

```xml
<dependency>
    <groupId>org.wiremock.integrations</groupId>
    <artifactId>wiremock-spring-boot</artifactId>
    <version>4.2.1</version>
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

## Hibernate 7: Fix Oracle-specific JPQL

**Fix Oracle-specific JPQL**: Replace `TO_DATE()` (Oracle function) with standard JDBC date literals:

```java
// Before (Oracle-specific)
@Query("... WHERE dok.opprettetDato >= TO_DATE('2022-01-01', 'yyyy-mm-dd')")

// After (standard JDBC date literal — works on all databases)
@Query("... WHERE dok.opprettetDato >= {d '2022-01-01'}")
```

## Third-party library compatibility

Some third-party libraries need specific versions for Boot 4:

| Library | Boot 3 version | Boot 4 version | Notes |
|---|---|---|---|
| `mq-jms-spring-boot-starter` (IBM MQ) | 3.x | **4.0.2+** | Major version bump for Boot 4 |
| `datasource-proxy-spring-boot-starter` | 1.12.x | **2.0.0+** | 1.x references old auto-config package paths |
| `logstash-logback-encoder` | 8.x | **9.0+** | Uses Jackson 3, compatible with Boot 4 |
| `token-support` (NAV) | 5.x | **6.0.4+** | Major version bump for Boot 4 |

## `SecurityAutoConfiguration` exclusion may be unnecessary

After Spring Boot modularization, `SecurityAutoConfiguration` is no longer included in the web package. It comes in via `spring-boot-starter-security-oauth2-client`, but if you use `spring-security-oauth2-client` directly instead, it won't be on the classpath. In that case, any `exclude = SecurityAutoConfiguration.class` can simply be removed.

## RestTestClient binding modes

If your tests need token-support `@Protected` annotations (or other interceptors) to be evaluated, you must bind `RestTestClient` with `.bindToServer()`. Otherwise, you can use `.bindToController(...)` which runs with significantly fewer resources.

Test dependency:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-resttestclient</artifactId>
    <scope>test</scope>
</dependency>
```

## Conflict between `microsoft-graph` and `token-validation-spring-test`

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

## Netty 4.2 compatibility

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

## Apache Camel is not yet compatible

As of Camel 4.17.0, Camel is not compatible with Spring Boot 4. Spring Boot 4 support in camel is expected in camel 4.19.0.

See: https://issues.apache.org/jira/browse/CAMEL-22463
