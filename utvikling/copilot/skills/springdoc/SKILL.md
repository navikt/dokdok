---
name: springdoc
description: >
  Skill for å halde orden på API-dokumentasjon for REST ved bruk av Springdoc for Spring Boot.
  Sørgjer for at alle endepunkt, responsar og HTTP-statusar er dekkja og dokumenterte, og skriven på bokmål.
---

## Kodestil — eksempel

### ✅ Godt annotert endepunkt

```java
@Operation(
    summary = "Hent journalpost",
    description = "Hentar ein journalpost basert på journalpostId",
    operationId = "hentJournalpost",
    tags = {"Journalpost"}
)
@ApiResponses({
    @ApiResponse(
        responseCode = "200",
        description = "Journalpost funnen",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(implementation = JournalpostResponse.class),
            examples = @ExampleObject(value = """
                {
                  "journalpostId": "123456789",
                  "tittel": "Søknad om dagpengar",
                  "status": "FERDIGSTILT"
                }
                """)
        )
    ),
    @ApiResponse(responseCode = "401", description = "Manglande eller ugyldig token"),
    @ApiResponse(responseCode = "403", description = "Manglande tilgang"),
    @ApiResponse(responseCode = "404", description = "Journalpost ikkje funnen"),
    @ApiResponse(responseCode = "500", description = "Intern feil")
})
@SecurityRequirement(name = "bearer-token")
@GetMapping("/journalpost/{journalpostId}")
public ResponseEntity<JournalpostResponse> hentJournalpost(
        @Parameter(description = "Unik ID for journalposten", example = "123456789")
        @PathVariable String journalpostId) {
    // ...
}
```

### ✅ Godt annotert DTO

```java
@Schema(description = "Respons med journalpostdata")
@Value
@Builder
public class JournalpostResponse {

    @Schema(description = "Unik ID for journalposten", example = "123456789")
    String journalpostId;

    @Schema(description = "Tittel på journalposten", example = "Søknad om dagpengar")
    String tittel;

    @Schema(description = "Status på journalposten", example = "FERDIGSTILT")
    String status;
}
```

## Praksisar

- Alle endepunkt skal ha `@Operation` med `summary`, `description` og `operationId`
- Bruk `tags` i `@Operation` for logisk gruppering av relaterte endepunkt
- Alle statuskoder som faktisk blir returnerte skal ha `@ApiResponse` (inkl. 401/403 for sikra endepunkt)
- Bruk `@SecurityRequirement` på endepunkt som krev autentisering
- Request-parametrar (`@PathVariable`, `@RequestParam`) skal ha `@Parameter` med `description` og `example`
- DTO-klasser skal ha `@Schema` på klassenivå (`description`) og på kvart felt (`description` + `example`)
- `@ExampleObject` på operasjonsnivå for rike/samansette eksempel, `@Schema(example=...)` på felt for enkle verdiar
- Bruk `@Content` for å knytte schema og eksempel til rett mediatype.
- Dersom responsen ikkje har ein body må ein ha med `content = @Content`
- Fiks bruk av deprekerte metoder frå springdoc

## Grenser

- ✅ **Alltid:** Legg til/oppdater Springdoc-annotasjonar, køyr `mvn clean package` for å verifisere
- ⚠️ **Spør fyrst:** Fiksing av deprekerte metoder, endringar i DTO-klasser, endringar i `config/`
- 🚫 **Aldri:** Endre forretningslogikk, endre testar, fjerne eksisterande funksjonalitet

## Output-format

Når du er ferdig, gi ein oppsummering:

```markdown
## Springdoc-rapport

### Endepunkt som vart dokumenterte
| Klasse | Metode | Statuskoder |
|--------|--------|-------------|
| JournalpostController | hentJournalpost | 200, 404, 500 |

### Manglar som gjenstår
- <beskriv eventuelle manglar du ikkje kunne fikse>

### Deprekerte metodar
- <list opp deprekerte metodar du fann, med forslag til erstatning>
```
