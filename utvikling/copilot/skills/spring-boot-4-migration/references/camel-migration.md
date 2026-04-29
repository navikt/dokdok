# Apache Camel Migration (Spring Boot 4)

Requires Camel **4.20.0+** for Boot 4.

Use a single `camel.version` property and import both the BOM and the dependencies POM:

```xml
<properties>
    <camel.version>4.20.0</camel.version>
</properties>

<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.apache.camel.springboot</groupId>
            <artifactId>camel-spring-boot-bom</artifactId>
            <version>${camel.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
        <dependency>
            <groupId>org.apache.camel.springboot</groupId>
            <artifactId>camel-spring-boot-dependencies</artifactId>
            <version>${camel.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

## MDC logging: `camel-mdc` module replaces `camel.main.use-mdc-logging`

Camel 4.20 extracted MDC logging into a separate module. Add the `camel-mdc` dependency and replace the property:

```xml
<dependency>
    <groupId>org.apache.camel</groupId>
    <artifactId>camel-mdc</artifactId>
</dependency>
```

```properties
# Before
camel.main.use-mdc-logging=true

# After
camel.mdc.enabled=true
```

If you had programmatic `context.setUseMDCLogging(true)`, remove it and use the property instead.

## JMS health indicator → `camelHealth`

Boot 4 removed `JmsHealthIndicator`. Replace with Camel's built-in:

```properties
# Before
management.endpoint.health.group.liveness.include=jms
# After
management.endpoint.health.group.liveness.include=camelHealth
```

## JMS tests: explicit `JmsTemplate` bean

Boot 4 no longer auto-configures `JmsTemplate` in tests with embedded Artemis:

```java
@TestConfiguration
public class JmsItestConfig {
    @Bean
    @DependsOn("broker")
    public JmsTemplate jmsTemplate(ConnectionFactory connectionFactory) {
        return new JmsTemplate(connectionFactory);
    }
}
```

## Embedded Kafka: remove hardcoded listeners

Kafka 4 (KRaft) assigns ports dynamically. Hardcoded listeners cause CI conflicts:

```java
// Before
@EmbeddedKafka(listeners = "PLAINTEXT://127.0.0.1:60172", ...)
// After
@EmbeddedKafka(...)
```
