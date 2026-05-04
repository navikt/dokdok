# P475.BREVSERVER_DLQ_PE

Dead letter queue for brevserver-nais. Har **ikke** automatisk resending.

## Fremgangsmåte

### 1. Finn meldingen i MQ

Åpne MQ-verktøyet → QueueManagers → Queues → `QA.P475.BREVSERVER_DLQ_PE`.

### 2. Finn journalpostId

```xml
<brevref>1234567890</brevref>
```

### 3. Søk i loggene

```
application:brevserver-nais AND message:"<journalpostId>"
```

## Feilscenarioer

### 4. Journalpost ikke funnet

```
no.nav.brevserver.core.exception.BrevTechnicalException:
Klarte ikke hente journalpost: Journalpost med id 1234567890 eksisterer ikke
```

Meldingen kan ha feilet fordi journalposten den skal kobles til er slettet (f.eks. av bjoark004).

**Fremgangsmåte:**
1. Sjekk om journalposten finnes i Joark — brevserver-nais kan ha problemer med å finne den selv om den eksisterer
2. Hvis den ikke finnes → undersøk logger for å finne årsak
3. Hvis slettet under "normale forhold" → flytt til `P_TRASH`
