# Copilot-ressurser

## Copilot instructions

Mappen `instructions/` inneholder to lag med instruksjoner:

| Fil/mappe                 | Lastes                                  | Formål                                            |
|---------------------------|-----------------------------------------|---------------------------------------------------|
| `copilot-instructions.md` | Alltid                                  | Tech stack, modulstruktur, arkitektur, git-regler |
| `scoped/`                 | Kun for relevante filer (via `applyTo`) | Domenespesifikke konvensjoner                     |

### Manuelt oppsett

Repo-wide instructions (symlink inn i `~/.copilot/`):

    ln -s ~/<path til dokdok-repoet>/utvikling/copilot/instructions/copilot-instructions.md ~/.copilot/

Alternativt, f.eks. om du allerede har en personlig instructions-fil, kan du redigere din `.zshrc` / `.bashrc` og legge til følgende:

    export COPILOT_CUSTOM_INSTRUCTIONS_DIRS="~/<path til dokdok-repoet>/utvikling/copilot/instructions/"

Path-scoped instructions i et applikasjonsrepo:

    ln -s ~/<path til dokdok-repoet>/utvikling/copilot/instructions/scoped <repo>/.github/instructions

Skills (brukernivå):

    ln -s ~/<path til dokdok-repoet>/utvikling/copilot/skills ~/.copilot/

Agents (brukernivå):

    ln -s ~/<path til dokdok-repoet>/utvikling/copilot/agents ~/.copilot/

### Oppsett med script

Bruk `setup.sh` for å sette opp symlinks automatisk i stedet for å gjøre det manuelt:

```bash
# Personlig oppsett: ~/.copilot/ (instructions, skills, agents)
~/<path til dokdok-repoet>/utvikling/copilot/setup.sh --personal

# Personlig + OpenCode (~/.config/opencode/)
~/<path til dokdok-repoet>/utvikling/copilot/setup.sh --all

# Scoped instructions i et applikasjonsrepo
~/<path til dokdok-repoet>/utvikling/copilot/setup.sh --repo ~/nav/min-app

# Kombiner
~/<path til dokdok-repoet>/utvikling/copilot/setup.sh --personal --repo ~/nav/min-app
```

Scriptet er idempotent — kjøres det på nytt skjer ingenting om symlinkene allerede er korrekte.

### Path-scoped instructions (lastes kun for relevante filer)

Filene i `scoped/` bruker `applyTo`-frontmatter for å begrense hvilke filer instruksjonene gjelder:

| Fil                              | Gjelder for                                |
|----------------------------------|--------------------------------------------|
| `general.instructions.md`        | Alle `.java`-filer                         |
| `database.instructions.md`       | Repository-klasser, migrasjoner, SQL       |
| `api.instructions.md`            | Endpoints, controllers, DataFetcher, Query |
| `anticorruption.instructions.md` | Anti-corruption layer, consumers           |
| `testing.instructions.md`        | Testklasser                                |
| `config.instructions.md`         | Config-klasser, `.properties`, NAIS-konfig |

> **Merk:** GitHub Copilot laster path-scoped instructions automatisk når du jobber med filer som matcher `applyTo`
> -mønsteret. Begge instruksjonslagene kombineres — repo-wide instruksjoner gjelder alltid, scoped instruksjoner legges
> til på toppen når relevant.

## Copilot Skills

Denne mappen inneholder [Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) som er dokumentert og vedlikeholdt av teamet.

Skills lastes inn on-demand av Copilot når de er relevante for det du spør om.

Det finnes to steder skills kan plasseres:

| Plassering                 | Scope                                      | Sti                                           |
|----------------------------|--------------------------------------------|-----------------------------------------------|
| **Personlig** (brukernivå) | Tilgjengelig i alle repoer på maskinen din | `~/.copilot/skills/<skill-navn>/SKILL.md`     |
| **Repo-nivå**              | Tilgjengelig for alle som jobber i repoet  | `<repo>/.github/skills/<skill-navn>/SKILL.md` |

Bruk `setup.sh --personal` eller symlink manuelt — se avsnittet om oppsett over.

### Tips

- Du kan sjekke hvilke skills som er lastet inn ved å bruke `/skills list`-kommandoen i copilot-cli.
- Om du legger til eller oppdaterer en skill kan du laste skills på nytt med `/skills reload`-kommandoen i copilot-cli.
- Mappenavnet må matche `name`-feltet i YAML-frontmatteren i `SKILL.md`, være lowercase, og bruke bindestrek.

## Tilgjengelige skills

| Skill                                                              | Beskrivelse                                                                                           |
|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [migrate-to-restclient](skills/migrate-to-restclient/SKILL.md)     | Guide for migrering fra WebClient/RestTemplate til RestClient med NAIS Texas-tokenveksling            |
| [owasp-top-10-2025](skills/owasp-top-10-2025/SKILL.md)             | Sikkerhetsregler basert på OWASP Top 10:2025 — tilgangskontroll, injeksjon, kryptografi, logging m.m. |
| [spring-boot-4-migration](skills/spring-boot-4-migration/SKILL.md) | Guide for migrering av NAV/NAIS Spring Boot 3-applikasjoner til Spring Boot 4                         |
| [dokvakt](skills/dokvakt/SKILL.md)                                 | Vaktguide for Team Dokumentløsninger — MQ-køfeil, DB-patching, distribusjons- og skanningavvik        |
| [springdoc](skills/springdoc/SKILL.md)                             | Held API-dokumentasjon for REST ved bruk av Springdoc for Spring Boot oppdatert                       |

## Copilot Agents

Agenter er mer selvstendige enn skills — de utfører en hel arbeidsflyt fremfor å bare gi veiledning.

Agenter plasseres i `~/.copilot/agents/<agent-navn>/AGENT.md` (brukernivå) eller `<repo>/.github/agents/<agent-navn>/AGENT.md` (repo-nivå).

Bruk `setup.sh --personal` eller symlink manuelt — se avsnittet om oppsett over.

### Tilgjengelige agenter

| Agent                                                  | Beskrivelse                                                                                                                           |
|--------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| [local-code-review](agents/local-code-review.agent.md) | Gjennomgår lokale endringer mot head-branch — sjekker lesbarhet, ansvarsdeling, navngiving og OWASP Top 10-sikkerhet                  |
| [dokvakt](agents/dokvakt.agent.md)                     | Vaktassistent for Team Dokumentløsninger — feilsøking av MQ-køer, DB-patching, distribusjons-/skanningavvik, med steg-for-steg-guider |
| [springdoc](agents/springdoc.agent.md)                 | Sjekk at Springdoc er sett opp skikkeleg og dokumenterer alle responsar                                                               |
