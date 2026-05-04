# QDOK001_FUNKSJONELL_FEIL

Funksjonell feilkø for dokprod (dokumentproduksjon). Har **ikke** automatisk resending.

## Fremgangsmåte

### 1. Finn meldingen i MQ

Åpne MQ-verktøyet → QueueManagers → Queues → `QDOK001_FUNKSJONELL_FEIL`.

### 2. Finn bestillingsId

Hent bestillingsId fra meldingen:

```xml
<bestillingsId>dba70fcb-fca4-47d9-8b4a-fada0cb50666</bestillingsId>
```

### 3. Søk i loggene

```
application:dokprod AND namespace:default AND message:"<bestillingsId>"
```

## Feilscenarioer

### 3a. Person registrert som død

Denne feilen inntreffer ikke lenger — forsøk på å produsere brev til avdøde stoppes nå uten at meldingen havner på feilkø.

### 3b. UKJENT_ADRESSE

Feilmelding:
```
TREG001 Kunne ikke mappe postadresse for mottaker fordi gjeldendePostadressetype=UKJENT_ADRESSE
```

Eller:
```
One of '{"http://nav.no/dok/brevdata/felles/v1/NAVFelles":poststed}' is expected.
```

**Tiltak for utbetalingsmeldinger (dokumenttypeId 000093/000095) og endringsoppgaver (000077/000112):**
- Flytt til `P_TRASH` uten videre håndtering
- Ingen behov for å varsle fagsystem — de kan ikke gjøre noe med dette

**For andre brevtyper:**
- Berørt fagside må informeres om adresseproblematikken

### 3c. Andre feil fra TREG001

Hvis `FUNCTIONAL_ERROR_REASON` **ikke** er "Kall mot TREG001 feilet med statusKode=400" → feilen må analyseres nærmere.

### 3d. SchemaValidationException / feilvalidering av brevdata

Feilmelding inneholder `SchemaValidationException:` eller `validering av brevdat feilet`.

Ulike rutiner avhengig av brevtype:

#### 1) Infotrygdbrev (dokumenttypeId 000045/000046)

Skal **ikke** meldes via Team-CCM. Flytt til kø `P_DOKPROD.QDOK001_FUNKSJO_FEIL_LAV_TEMP_MMA_4387`.

#### 2) Pesysbrev (dokumenttypeId 000073/000076)

Skal **ikke** meldes via Team-CCM. Flytt til kø `P_DOKPROD.QDOK001_FUNKSJONELL_FEIL_LAV_PESYS`.

#### 3) Utbetalingsmeldinger med forbigående feil

Feilmelding av typen:
```
TREG001 Funksjonell feil: Feil i MottakerPlugin med feilmelding=Mottakerdata mangler mottakerId
```
eller:
```
TREG001 Funksjonell feil: Feil i SakspartPlugin med feilmelding=Sakspart mangler AktoerTypeKode
```

**Tiltak:** Forbigående feil — legg meldingene tilbake på opprinnelig kø.

#### 4) Brev bestilt av TØB (utbetalingsmeldinger/endringsoppgaver)

Håndteres som beskrevet i punkt 3b.

#### 5) Øvrige brev — informer Team CCM

Post lenke til ATOM-saken på #team_ccm med ledetekst "Feilvalidering av brevdata inntruffet i Prod".

Team CCM vil analysere videre og enten:
- Gi tilbakemelding til konsument/fagsystem om årsak
- Korrigere feil i meldingssyntaks før resending

### 3e. DokumenttypeId 000120 — validering feilet

**Tiltak:** Flytt meldingene til `P_TRASH` uten videre håndtering.

Unntak: Hvis dette skjer i forbindelse med den årlige batchen BPEN056 (slutten av november) — gi beskjed til Team Pensjonbrev.

### 4. Ta meldingene av MQ-kø

Bestill via Atom-sak, eller bruk MQ-verktøyet direkte (IBM MQ Administrator via remote desktop).
