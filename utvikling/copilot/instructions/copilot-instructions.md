# Copilot Instructions

## Behaviour
- ** Be direct and not verbose. Do not appear to be thinking, do not use filler words. Be short, concise, and avoid seeming like a human.
- ** Instead of saying "◐ The user wants" say "I will". Do not speak in third person, just explain what you are about to do.

## Tech Stack

- **Java 25** (latest LTS)
- **Spring Boot 4.x.x** (parent POM)
- **Maven** (multi-module)
- **Spring Resilience** for retries
- **Lombok** (`@Value`, `@Builder`, `@Slf4j`)
- **BlazeJpa** (new), **Hibernate** (if present already)
- **Redis/Valkey** (distributed cache), **Caffeine** (local cache)
- **JSpecify**, **Jakarta Validation**
- **JUnit 5**, **Mockito**, **Wiremock**, **TestRestClient**

## Module Structure

| Module | Purpose |
|---|---|
| `app` | Boot entrypoint, GraphQL/REST endpoints, wiring |
| `core` | Shared domain, anti-corruption, access control, config |
| other | Feature modules with clear boundaries |

All feature modules depend on `core`. Only `app` depends on all modules.

## Package Structure

The base package is `no.nav.<app-name>`. Key sub-packages:

- `anticorruptionlayer/` — external integrations/adapters
- `domain/kode/` — enum code tables
- `query/` — GraphQL DataFetcher + Query + Service
- `endpoints/graphql/` — GraphQL controller and wiring
- `endpoints/rest/` — REST controllers
- `config` — config values + validation only

## Architecture Patterns

### Anti-Corruption Layer
Each external system has a dedicated anti-corruption layer that translates external DTOs into internal domain models. Never leak external DTOs into domain logic.


## Coding Conventions

### General
- Use **Lombok** (`@Builder`, `@Slf4j`)
- Use parameterized logging, never string concat
- Prefer immutability (record / `@Value`)
- Use `Optional<T>` for nullable return values
- Use strict Jakarta Bean Validation on config classes + tests
- Avoid creating an interface if it will only be implemented by one class
- Prefer typed objects over primitives/strings in params
- Use `java.time`; avoid `java.sql.Date` / `java.util.Date`
- Use JSpecify nullness declarations
- Use `_` for unused vars (Java 22+)
- Static imports for test asserts/utilities (not `List.of`/`Map.of`)
- Comments/error text preferably Norwegian; keep technical terms in English
- Prefer `"...%s...".formatted()` over `String.format()`

### Database
- PK names: full table name (without prefix) + `id` (`t_dokument_info` -> `dokument_info_id`)
- Replace Norwegian letters in DB names: `æ->e`, `ø->o`, `å->a`
- `VARCHAR2` sizes: `128`, `512`, `4000` char; use `CLOB` above `4000`
- Use `DATE` by default, `TIMESTAMP` only when needed
- Java-to-Oracle mapping:

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

Document with SpringDoc OpenAPI annotations.

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
- Wrap annotation names in backticks in commit messages/docs (e.g. `@Retryable`)
- Keep commit messages short (single imperative line preferred)

## Building & Testing

Use `mvn clean verify` to run all tests.

```bash
mvn clean verify         # compile + unit tests + integration tests
```

Tests use:
- Wiremock for mocking external APIs
- Token Validation Spring Test for generating test JWT tokens
