---
name: owasp-top-10-2025
description: Security guidance based on the OWASP Top 10:2025 list. Use this when writing or reviewing code for security vulnerabilities, hardening applications, implementing access control, input validation, error handling, cryptography, authentication, logging, or secure design. Also use when asked about OWASP, application security, secure coding practices, or common web application vulnerabilities.
---

# OWASP Top 10:2025

Apply these rules when writing or reviewing code. Source: [OWASP Top 10:2025](https://owasp.org/Top10/2025/).

| # | Risk | Rules |
|---|------|-------|
| A01 | Broken Access Control | Deny by default; enforce record ownership in service layer; test access controls |
| A02 | Security Misconfiguration | No defaults/samples in prod; no secrets in code; suppress error details |
| A03 | Supply Chain Failures | Pin deps; scan for CVEs; remove unused deps; harden CI/CD |
| A04 | Cryptographic Failures | TLS 1.2+ only; `SecureRandom` not `Random`; Argon2/scrypt for passwords; no MD5/SHA1 |
| A05 | Injection | Parameterized queries only; never concatenate user input into queries/commands |
| A06 | Insecure Design | Threat model critical flows; validate at every tier; segregate tenants |
| A07 | Authentication Failures | Enforce MFA; no default creds; validate JWT `aud`/`iss`/scopes; rate-limit logins |
| A08 | Integrity Failures | Verify signatures; trusted repos only; avoid Java serialization of untrusted data |
| A09 | Logging & Alerting | Log security events with context; never log PII/secrets; encode log data; alert on anomalies |
| A10 | Exceptional Conditions | Fail closed; centralized `@RestControllerAdvice`; rate-limit; never expose stack traces |

---

## A01 — Broken Access Control

- **Deny by default** — explicitly grant access, never implicitly allow
- Enforce **record ownership** in service layer, not just URL-level checks
- Access control on all API methods (POST, PUT, DELETE), not just GET
- Log access control failures; alert on repeated failures
- Short-lived JWTs; invalidate sessions server-side on logout
- Test access controls in unit/integration tests

```java
public JournalpostDto hentJournalpost(String journalpostId, String innloggetBruker) {
    var journalpost = journalpostRepository.findById(journalpostId)
        .orElseThrow(() -> new RessursIkkeFunnetException("Journalpost ikke funnet: %s".formatted(journalpostId)));
    if (!tilgangskontroll.harTilgang(innloggetBruker, journalpost)) {
        throw new ManglerTilgangException("Bruker har ikke tilgang til journalpost: %s".formatted(journalpostId));
    }
    return journalpostMapper.tilDto(journalpost);
}
```

## A02 — Security Misconfiguration

- Remove unused features, endpoints, samples, default accounts
- Use NAIS Texas / short-lived credentials — never static keys in code/config
- Send security headers (HSTS, CSP, X-Content-Type-Options)
- Identical hardening across dev/QA/prod (different credentials)

```properties
server.error.include-stacktrace=never
server.error.include-message=never
server.error.include-binding-errors=never
management.endpoints.web.exposure.include=health,info,prometheus
```

## A03 — Supply Chain Failures

- Pin dependency versions in `dependencyManagement`; track transitive deps
- Run `mvn org.owasp:dependency-check-maven:check` or equivalent in CI
- Remove unused dependencies to reduce attack surface
- Only use trusted repos; prefer signed packages
- Harden CI/CD: branch protection, separation of duties, signed builds, no committed secrets

## A04 — Cryptographic Failures

- **TLS 1.2+** with forward secrecy; enforce HSTS
- Passwords: **Argon2, scrypt, or PBKDF2-HMAC-SHA-512**
- Authenticated encryption only (AES-256-GCM, ChaCha20-Poly1305) — never ECB
- Keys in HSM / cloud KMS — never in source code
- Discard sensitive data as soon as possible

```java
// ❌ var random = new Random();
// ✅
var secureRandom = SecureRandom.getInstanceStrong();
```

## A05 — Injection

- **Always parameterized queries** — never concatenate user input into SQL/HQL/JPQL/commands
- Server-side input validation; escape output as last resort
- Use SAST/DAST in CI/CD

```java
// ❌ "SELECT * FROM accounts WHERE custID='" + request.getParameter("id") + "'"
// ✅
@Query("SELECT a FROM Account a WHERE a.custId = :custId")
Optional<Account> findByCustId(@Param("custId") String custId);

// ❌ Runtime.getRuntime().exec("nslookup " + userInput);
// ✅ new ProcessBuilder("nslookup", validatedDomain);
```

## A06 — Insecure Design

- Threat model authentication, access control, business logic, and key flows
- Plausibility checks at every tier (frontend → backend)
- Test both use-cases and misuse-cases
- Segregate tiers and tenants by design
- Never enforce security only on client side

## A07 — Authentication Failures

- Enforce MFA; never deploy with default credentials
- Validate JWT claims: `aud`, `iss`, scopes
- Rate-limit failed logins; use consistent error messages to prevent enumeration
- Invalidate sessions on logout, idle, and absolute timeout
- NIST 800-63b: don't force password rotation unless breach suspected

```properties
spring.security.oauth2.resourceserver.jwt.issuer-uri=${AZURE_OPENID_CONFIG_ISSUER}
spring.security.oauth2.resourceserver.jwt.audiences=${AZURE_APP_CLIENT_ID}
```

## A08 — Software or Data Integrity Failures

- Verify digital signatures on artifacts and updates
- Use trusted repos only; consider internal vetted mirror
- Code and config changes must go through review
- Avoid Java `ObjectInputStream` on untrusted data — prefer Jackson with explicit types
- If Java serialization required: use `ObjectInputFilter` (JEP 290) with allow-list

## A09 — Security Logging and Alerting

- Log all login, access control, and validation failures with user context
- **Never log** passwords, tokens, fødselsnummer, credit card numbers
- Use parameterized logging (`{}`) — prevents log injection and avoids concatenation
- Structured JSON logs; append-only audit trails
- Alert on suspicious patterns; establish incident response playbooks

```java
// ✅ log.warn("Mislykket innlogging for bruker: {}, IP: {}", sanitize(brukernavn), request.getRemoteAddr());
// ❌ log.info("Bruker {} logget inn med passord {}", brukernavn, passord);
// ❌ log.info("Bruker: " + brukernavn);
```

## A10 — Mishandling of Exceptional Conditions

- **Fail closed** — always roll back partial transactions
- Centralized `@RestControllerAdvice` as global exception handler
- Never expose stack traces or internal error details to users
- Rate-limit, resource quotas, and throttling to prevent resource exhaustion
- Catch exceptions where they occur; handle meaningfully, don't swallow

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    @ExceptionHandler(FunctionalException.class)
    public ResponseEntity<FeilDto> handleFunctional(FunctionalException e) {
        log.warn("Funksjonell feil: {}", e.getMessage());
        return ResponseEntity.status(e.getHttpStatus()).body(new FeilDto(e.getBrukermelding()));
    }
    @ExceptionHandler(Exception.class)
    public ResponseEntity<FeilDto> handleUnexpected(Exception e) {
        log.error("Uventet feil", e);
        return ResponseEntity.internalServerError().body(new FeilDto("En uventet feil oppsto. Prøv igjen senere."));
    }
}
```
