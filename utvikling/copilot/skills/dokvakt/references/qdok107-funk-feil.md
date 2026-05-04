# QDOK107_FUNK_FEIL

Funksjonell feilkø for distribusjon bestilt fra dokprod. Har **ikke** automatisk resending.

## Fremgangsmåte

### 1. Finn meldingen i MQ

Åpne MQ-verktøyet → QueueManagers → Queues → `P_DOKPROD.QDOK107_FUNK_FEIL`.

### 2. Finn forsendelseId

```xml
<forsendelseId>1234567890</forsendelseId>
```

### 3. Søk i loggene

```
application:dokprod AND message:"forsendelseId=<forsendelseId>" AND level:"Warning"
```

### 4. Finn warn-melding

Se etter logginnslag som begynner med "Qdok107 funksjonell feil":

```
Qdok107 funksjonell feil, avslutter behandling forsendelseId=1234567890,
bestillingsId=<uuid>, journalpostid=1234098765:
no.nav.dokprod.core.consumer.saf.exception.SafFunctionalException:
Kall mot saf:hentdokument feilet funksjonelt med statusKode=404 NOT_FOUND
```

## Feilscenarioer

### 5a. Forbigående feil

Hvis feilen ser forbigående ut → flytt meldingen tilbake på `P_DOKPROD.QDOK107_BESTILL_DISTRIBUSJON`.

### 5b. Vedvarende feil — finn opphav

Koble til dokprod-databasen og bruk forsendelseId for å finne:
- `journalpost_id`
- `k_dist_kanal`
- `k_best_fagsystem`
- `k_fagomrade`
- `dokumenttype_id`

#### Ekspedisjonsbrev til Trygderetten (dokumenttypeid 000142)

Hvis `k_dist_kanal` er Trygderetten → kontakt Styringsenhet Klageinstans for å avklare veien videre.

Hvis de spør om forsendelsen må bygges på nytt: svaret er i utgangspunktet ja, men det er mulig å fjerne problematiske vedlegg fra forsendelsen manuelt i databasen.
