---
applyTo: "**/*Test.java,**/*IT.java,**/test/**/*.java"
---

# Testing Conventions

- Static imports for test asserts/utilities (not `List.of`/`Map.of`)
- Use strict Jakarta Bean Validation on config classes + tests
- **Wiremock** for mocking external APIs
- **Token Validation Spring Test** for generating test JWT tokens
- **TestRestClient** for REST endpoint testing
- **JUnit 5** + **Mockito** for unit tests
