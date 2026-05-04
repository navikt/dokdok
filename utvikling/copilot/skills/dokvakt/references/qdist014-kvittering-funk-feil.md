# QDIST014_KVITTERING_FUNK_FEIL

Funksjonell feilkø for DPI-kvitteringer. Har **ikke** automatisk resending.

La meldingene ligge til neste dag før manuell analyse.

## Feilscenarioer

### 1. Ugyldig forsendelseId (null)

```
Rdist001AdminstrerForsendelseFunctionalException: Kall mot rdist001 -
hentForsendelse feilet med statusCode=400 BAD_REQUEST,
feilmelding=Ugyldig input: Feltet forsendelseId må være et tall. Fikk forsendelseId=null
```

Denne feilen oppstår når forsendelse til DigDir er utført men kvitteringsløpet har feilet. Dokdist-databasen må patches slik at kvitteringen går gjennom.

#### Fremgangsmåte

**1) Finn opprinnelig forsendelse_id fra loggene:**

```
application:dokdistdpi AND cluster:prod-fss AND "konversasjon_id"
```

Alternativt: sjekk `qdist011_boq` for en melding fra samme tidspunkt.

**2) Finn distribusjon_info_id fra dokdist-databasen:**

```sql
select do.dokument_info_id, do.konversasjon_id, di.distribusjon_info_id,
       di.distribusjon_dato, do.arkivkode, di.k_dist_kanal,
       di.k_dist_status, do.k_dokument_status, do.endret_dato
from distribusjon_info di
join dokument_info do on di.distribusjon_info_id = do.distribusjon_info_id
where do.dokument_info_id in (<forsendelse_id>);
```

**3) Bestill databasepatching:**

Tre mulige scenarioer:
- **Status og konversasjonsId mangler** → patch begge
- **Status OK (OVERSENDT), kun konversasjonsId mangler** → patch kun konversasjonsId
- **Både status og konversasjonsId er på plass** → kun resending uten patching (gå til steg 4)

**4) Resend melding:**

Legg meldingen på køen `QDIST014_KVITTERING_FRA_DPI`.

**5) Rydd opp:**

Slett eventuell melding på `DOKDISTDPI.QDIST011_DIST_TIL_DPI_BOQ` med samme forsendelse_id.
