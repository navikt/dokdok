---
applyTo: "**/endpoints/**/*.java,**/*Controller*.java,**/*DataFetcher*.java,**/*Query*.java"
---

# API Conventions

## REST

- Document all endpoints with SpringDoc OpenAPI annotations

## GraphQL

- `*Query` — orchestrator that coordinates services and returns domain objects
- `*DataFetcher` — resolves individual fields, delegates to a Query or Service
- `*Service` — business logic, called by both Query and DataFetcher
