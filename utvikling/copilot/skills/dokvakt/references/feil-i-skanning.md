# Feil i skanmot-appene

Dersom det skjer en teknisk eller funksjonell feil i skanmot-appene vil det bli varslet om dette i `#dokhendelser` på Slack. Forslag til feilsøking finnes under.

## Fremgangsmåte

### Søk i loggene

Alle skanmot-apper er funksjonelt like — fremgangsmåten gjelder for alle.

**Søk i loggene** etter filnavnet (uten .pdf), en dag eller to før datoen i filnavnet:

```
OVRIG_16.11.2022_R511796699_4_1284
```

### Undersøk filene inne på vdi-utvikler-dokumentloesninger

Bruk WinSCP og logg inn på sftp-serveren. Host og brukernavn finner du i Nav-console for en av skanmot-appene, og du trenger også en personlig ssh-nøkkel. Her ligger mapper navngitt `SKANMOT<APPNAVN>_FEIL`, f.eks. `SKANMOTOVRIG_FEIL`.
Sjekk ut hva som ligger i mappen for appen du er interessert i. Inni mappen ligger mapper navngitt etter batchen som ble kjørt, f.eks. `11.06.2026_R123400368_1_4437912`, og inni der igjen
ligger zippede mapper for dokumentene som har feilet. Husk at filene på feilområdet må bli slettet etter at feilen er fikset.

### Ulike situasjoner som kan oppstå
- Filer med feil metadata (f.eks. fil som heter `OVRIG_.pdf`). Vil ofte gi 409 CONFLICT i appen.

#### Epost-mal: Feil metadata i filnavn

```
Emne: Nav mottok fil fra <SKANMOT-app> <dd.mm> med feil metadata

Hei Iron Mountain

En av filene i batch <BATCH_NAVN> har feil metadata med filnavn <FILNAVN>.
Kan dere sjekke ut dette?
```
