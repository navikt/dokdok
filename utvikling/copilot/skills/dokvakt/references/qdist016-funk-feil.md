# QDIST016_FUNK_FEIL

Funksjonell feilkø for dokdistdpv — sender meldinger til virksomheter via Digital Post for virksomheter (DPV) i Altinn.

Har **IKKE** automatisk resending.

> **NB:** `forsendelseId` i QDIST016 er feltet `dokument_info.dokument_info_id` i dokumentdistribusjonsdatabasen — har ingenting å gjøre med Forsendelse i dokprod.

## Fremgangsmåte

### 1. Finn forsendelseId

```xml
<forsendelseId>12345678</forsendelseId>
```

### 2. Søk i loggene

```
application:dokdistdpv AND level:Warning AND message:"forsendelseId=<forsendelseId>"
```

Velg tidsrommet rundt treffet, fjern `AND message:...`-delen, og se på den andre warn-meldingen for å finne hva som gikk galt.

## Feilscenarioer

### 3. Teknisk feil fra Altinn

```
Distribusjon til Altinn feilet med feilmelding=Your request suffered from a
non-functional error. If this persist, please report it to the system administrator.
Please include the id concerning this speciffic error [...uuid...]. og guid=...uuid...
```

**Tiltak:** Legg meldingen tilbake på `P_DOKDISTDPV.QDIST016_DIST_TIL_DPV`. Vil mest sannsynlig gå gjennom.

Hvis den feiler igjen → kontakt Altinn med feilmeldingen (inkluder UUIDs).
