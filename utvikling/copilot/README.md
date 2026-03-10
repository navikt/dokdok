# Copilot Skills

Denne mappen inneholder [Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) som er dokumentert og vedlikeholdt av teamet.

Skills lastes inn on-demand av Copilot når de er relevante for det du spør om.

## Bruke skills lokalt

Det finnes to steder skills kan plasseres:

| Plassering | Scope | Sti |
|------------|-------|-----|
| **Personlig** (brukernivå) | Tilgjengelig i alle repoer på maskinen din | `~/.copilot/skills/<skill-navn>/SKILL.md` |
| **Repo-nivå** | Tilgjengelig for alle som jobber i repoet | `<repo>/.github/skills/<skill-navn>/SKILL.md` |

### Oppsett for personlig bruk

1. Du kan bruke symlinks for å automatisk oppdatere skills fra dokdok-repoet i
   din lokale mappe når du puller endringer fra repoet (dette funker i hvert fall på linux og macOS):

       ln -s ~/<path til dokdok-repoet>/utvikling/copilot/skills ~/.copilot/

   Eventuelt kan du linke inn enkelt skill om du også har skills fra andre steder:

       ln -s ~/<path til dokdok-repoet>/utvikling/copilot/skills/spring-boot-4-migration ~/.copilot/skills/spring-boot-4-migration


1. Det er også mulig å bare kopiere ønsket skill-mappe til din lokale `~/.copilot/skills/`-mappe:

   ```
   ~/.copilot/
   └── skills/
       └── spring-boot-4-migration/
           └── SKILL.md
   ```

2. Mappenavnet må matche `name`-feltet i YAML-frontmatteren i `SKILL.md`, være lowercase, og bruke bindestrek.

3. Start Copilot CLI på nytt for å laste inn nye skills.

### Tips

- Du kan sjekke hvilke skills som er lastet inn ved å bruke `/skills list`-kommandoen i copilot-cli.
- Om du legger til eller oppdaterer en skill kan du laste skills på nytt med `/skills reload`-kommandoen i copilot-cli.

## Tilgjengelige skills

| Skill | Beskrivelse |
|-------|-------------|
| [spring-boot-4-migration](skills/spring-boot-4-migration/SKILL.md) | Guide for migrering av NAV/NAIS Spring Boot 3-applikasjoner til Spring Boot 4 |
