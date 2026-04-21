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
