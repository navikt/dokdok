---
applyTo: "**/*.java"
---

# General Coding Conventions

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
- Comments/error text preferably Norwegian; keep technical terms in English
- Prefer `"...%s...".formatted()` over `String.format()`

## Naming

- `*Dto` — data transfer objects
- `*Mapper` — model-to-model mappers
- `*AntiCorruptionLayer` — external system adapters
- `*Service` — business logic
- `*Query` — GraphQL query orchestrator
- `*DataFetcher` — GraphQL field resolver
- `*Repository` — domain model access
- `*Coordinator` / `*CoordinatorImpl` — complex workflow orchestration
- `*Code` — code table enums

## Exception Handling

- `...TechnicalException` — system/infrastructure errors (maps to 500)
- `...FunctionalException` — business logic errors (maps to 4xx)
