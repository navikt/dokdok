# Copilot Instructions

## Tech Stack

- **Java 25** - always use latest LTS java version
- **Spring Boot 4.x.x** (parent POM)
- **Maven** multi-module build
- **Spring Resilience** for retries
- **Lombok** (`@Value`, `@Builder`, `@Slf4j`)
- **BlazeJpa** (new projects), **Hibernate** (if already present) for database-queries
- **Redis/Valkey** for distributed caching, **Caffeine** for local caching
- **JSpecify** for declaration of nullability
- **Jakarta Validation** validation of configuration propeties etc
- **JUnit 5**, **Mockito**, **Wiremock**, **TestRestClient** for testing

## Module Structure

| Module | Purpose |
|---|---|
| `app` | Spring Boot application entry point, GraphQL & REST controllers, wiring |
| `core` | Shared domain models, anti-corruption layers, access control, config |
| other | Make other modules as required - try to encapsulate features in a logical way |

All feature modules depend on `core`. Only `app` depends on all modules.

## Package Structure

The base package is `no.nav.<app-name>`. Key sub-packages:

- `anticorruptionlayer/` — integration with external systems (Joark, PDL, SAK, FPSAK, K9SAK, Bisys, Pensjon, MS Graph, Entra Proxy, Tilgangsmaskinen, etc etc)
- `domain/kode/` — enum code tables (Tema, Journalposttype, Journalstatus, etc.)
- `query/` — GraphQL DataFetcher + Query + Service classes per query type
- `endpoints/graphql/` — GraphQL controller and wiring
- `endpoints/rest/` — REST controllers
- `config` - classes holding configuration values and validation for those, but nothing else

## Architecture Patterns

### Anti-Corruption Layer
Each external system has a dedicated anti-corruption layer that translates external DTOs into internal domain models. Never leak external DTOs into domain logic.


## Coding Conventions

### General
- Use **Lombok** annotations: `@Builder` for construction, `@Slf4j` for logging
- Use **parameterized logging**: `log.info("Fetching journalpost: {}", id)` — never string concatenation
- Prefer **immutability** — use Java records, or lombok `@Value` (final fields, no setters)
- Use `Optional<T>` for nullable return values
- Use Jakarta Bean Validation (`@NotBlank`, etc) on configuration classes. Make validation as strict as possible. Create tests that check that the constraints are actually validated.
- Avoid creating an interface if it will only be implemented by one class
- Prefer objects over primitives over Strings as parameters
- use the modern java.time-package, avoid java.sql.Date, avoid java.util.Date
- Use jspecify for declaration of nullness
- Use `_` for unused variables (unnamed variables, Java 22+)
- Use static imports when possible for test assertions and utilities (e.g. `assertThat`, `mockStatic`) — but not for factory methods like `List.of`, `Map.of`
- Comments and error messages should preferably be in Norwegian, but keep technical terms in English (e.g. "null", "exception", "timeout")
- Prefer `"..%s..".formatted()` over `String.format()` and string concatenation

### Database
- primary keys should have a name that consists of the entire table name (except prefix), and ends in "id". E.g. for `t_dokument_info` primary key is named `dokument_info_id`
- Norwegian letters should be substituted as follows in database object names: "æ" -> "e", "ø" -> "o", "å" -> "a"
- Varchar2-fields should be one of these sizes: either 128 char (small, for enums, statuses, UUIDs etc), 512 char (medium, for document titles and short texts), 4000 char (large text fields). Specify sizes in char. Use CLOB for fields over 4000 characters.
- For time / date-types, use DATE by default, or TIMESTAMP if the extra precision is required.
- Map java-types to oracle db fields as follows:

  | JAVA TYPE | ORACLE DATABASE TYPE |
  |-----------|--------------------------|
  | boolean, java.lang.Boolean | NUMBER(1) |
  | int, java.lang.Integer | NUMBER(10) |
  | long, java.lang.Long | NUMBER(19) |
  | float, java.lang.Float | NUMBER(19,4) |
  | double, java.lang.Double | NUMBER(19,4) |
  | short, java.lang.Short | NUMBER(5) |
  | byte, java.lang.Byte | NUMBER(3) |
  | enums, java.lang.String | VARCHAR2(n char) |
  | java.lang.Number | NUMBER(38) |
  | java.math.BigInteger | NUMBER(38) |
  | java.math.BigDecimal | NUMBER(38) |
  | byte[], java.lang.Byte[], java.sql.Blob | BLOB |


### Naming
- `*Dto` — data transfer objects
- `*Mapper` — model-to-model mappers
- `*AntiCorruptionLayer` — external system adapters
- `*Service` — business logic
- `*Query` — GraphQL query orchestrator
- `*DataFetcher` — GraphQL field resolver
- `*Repository` — domain model access
- `*Coordinator` / `*CoordinatorImpl` — complex workflow orchestration
- `*Code` — code table enums

### Exception Handling
- `...TechnicalException` — system/infrastructure errors (maps to 500)
- `...FunctionalException` — business logic errors (maps to 4xx)


## REST API

Should be documented with SpringDoc OpenAPI annotations.

## Configuration

- `app/src/main/resources/application.properties` — core settings
- `app/src/main/resources/application-nais.properties` — NAIS/production overrides
- `nais/naiserator.yaml` — Kubernetes deployment manifest (templated)
- `nais/q*-config.json` / `nais/p-config.json` — environment-specific config

Key config classes: `<app-name>Properties`, `AzureProperties`, `NaisProperties`, `WebProxyProperties`.

## Git & Workflow

- **All changes are local only.** Do not push to remote branches, create remote branches, or open pull requests.
- Committing locally is allowed and encouraged.
- The developer will review changes and handle pushing/PR creation manually.
- Do not run `git push`, `gh pr create`, or any command that modifies the remote repository.
- When mentioning annotations or anything starting with `@` in commit messages or documentation, wrap them in backticks (e.g. `@Retryable`, `@Builder`).
- Keep commit messages short and concise — a single imperative summary line is preferred.

## Building & Testing

Use `mvn clean verify` to run all tests.

```bash
mvn clean verify         # compile + unit tests + integration tests
```

Tests use:
- Wiremock for mocking external APIs
- Token Validation Spring Test for generating test JWT tokens

