# Distribusjonsavvik

Håndtering av forsinkelser i distribusjon til ulike kanaler.

## Bakgrunn

DokdistAvstemming kjører mandag, onsdag og fredag kl 11:00. Dersom forsendelser ikke er kvittert innen frist, opprettes Jira-oppgaver. Jira-sakene har Excel-vedlegg med forsendelsene som skal følges opp.

### Nyttige SQL-er

**Forsinkede forsendelser per kanal:**

```sql
-- Tilpass med ønsket kanal og datoperiode
select di.k_dist_kanal, di.k_dist_status, do.k_dokument_status, count(*)
from distribusjon_info di
join dokument_info do on di.distribusjon_info_id = do.distribusjon_info_id
where di.k_dist_kanal = '<kanal>'
  and di.k_dist_status not in ('EKSPEDERT', 'FEILET')
group by di.k_dist_kanal, di.k_dist_status, do.k_dokument_status;
```

**Alle forsendelser for gitte journalposter:**

```sql
-- dokument_info_id  = forsendelseId i avviksrapporten
-- distribusjon_id = bestillingsId/distribusjonId i avviksrapporten
-- arkivkode    = journalpostId
select di.distribusjon_id, di.k_dist_kanal, di.k_dist_status,
       do.dokument_id, do.k_dokument_status, do.arkivkode as journalpost_id,
       di.distribusjon_dato
from distribusjon_info di
join dokument_info do on di.distribusjon_info_id = do.distribusjon_info_id
where do.arkivkode in ('<journalpostId>')
order by do.arkivkode, di.distribusjon_dato;
```

---

## 1. Distribusjonsavvik PRINT

To verdikjeder distribuerer til sentral print:
1. **AFP-print fra Doksys** — batch via BMF001, BDOK002, BDIST005
2. **PDF-print fra Dokumentdistribusjon** — via QDIST008 og QDIST009

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| KLAR_FOR_DIST | KLAR_FOR_DIST | Feilet i QDIST009 / ligger på backoutkø. Forsøk rekjøring først. Sjekk logger. Ved vedvarende funksjonell feil: ta av kø, patch status til FEILET, meld fra til bestiller. |
| OVERSENDT | BEKREFTET | PDF-print: bekreftet mottatt men ikke kvittert EKSPEDERT. Etterlys status hos Skatteetaten — oppgi `dokumentId` (mailpieceId). |
| BEKREFTET | OVERSENDT | AFP-print: bekreftet mottatt men ikke kvittert EKSPEDERT. Samme oppfølging som over. |
| OVERSENDT | OVERSENDT | Skatteetaten har ikke bekreftet mottak. Kjent problem, trolig filsluse. |
| OVERSENDT/BEKREFTET | EKSPEDERT | Happy case — printet, pakket og levert til posten. |

---

## 2. Distribusjonsavvik SDP/DPI

Distribusjon via Digdir til DigiPost/e-Boks. De fleste avvik skyldes forsinkede/manglende kvitteringer fra e-Boks.

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| KLAR_FOR_DIST | KLAR_FOR_DIST | Feilet i QDIST011, ligger på backoutkø `P_DOKDISTEFORMIDLING.QDIST011_DIST_TIL_DPI_BOQ`. Forsøk rekjøring. Ved vedvarende feil: ta av kø, patch til FEILET, meld til bestiller. |
| OVERSENDT | OVERSENDT | Sendt til Digdir men ingen bekreftelse innen frist. Etterlys status hos Digdir — oppgi `KONVERSASJON_ID`. |
| EKSPEDERT | EKSPEDERT | Happy case — bekreftelse fra postkasseleverandør mottatt. |

---

## 3. Distribusjonsavvik E-HANDEL

Distribusjon til NETS av e-fakturaer fra OEBS, ELIN og PREDATOR. Avvik er sjeldne. Kvitteringer ankommer ofte noen timer etter rapportering — sjekk status manuelt før purring.

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| OVERSENDT | OVERSENDT | Sendt til NETS, men ingen bekreftelse innen frist. |
| FEILET | FEILET | Sjekk `feilkvittering.detaljer`. Typiske feil: "Receiver not found", "B2C issuer blocked", "Ugyldig forfallsdato". Teamet trenger **ikke** varsle — NETS varsler via "Daily forsendelsesrapport" og avvikene håndteres av OEBS/SITS. |
| BEKREFTET | EKSPEDERT | Happy case. |

---

## 4. Distribusjonsavvik TRYGDERETTEN (eller DPO med trygderettens orgnr)

Forsendelser behandles av QDIST013 via Altinn Meldingsformidler. Kvitteringer mottas normalt innen minutter (sdist001 sjekker hvert 10. minutt). DokdistAvstemming rapporterer etter 6 timer.

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| KLAR_FOR_DIST | KLAR_FOR_DIST | Feilet i QDIST013, ligger på `P_DOKDISTEFORMIDLING.QDIST013_DIST_TRYGDE_BOQ`. Forsøk rekjøring. Ved vedvarende feil: ta av kø, patch til FEILET, meld til Klageinstans. |
| OVERSENDT | OVERSENDT | Sendt til Altinn men ikke bekreftet. Varsle Trygderetten og Klageinstans. Kan bety at integrasjonspunktet har stoppet. Ved rekjøring: patch status til KLAR_FOR_DIST, legg melding på kø til QDIST013. |
| BEKREFTET | BEKREFTET | Mottatt av integrasjonspunkt men ikke bekreftet av sak/arkiv-system. Varsle Trygderetten og Klageinstans. |
| EKSPEDERT | EKSPEDERT | Happy case. |

Se også: `trygderetten-kvitteringer.md` for detaljert oppfølging av manglende kvitteringer.

## 5. Distribusjonsavvik DITTNAV

Start med å sjekke i dokumentdistribusjon-databasen distribusjonsstatus og dokumentstatus for de aktuelle forsendelsene.

Dersom status er OVERSENDT, sjekk med minside-varsler på Slack om de kan se noe rart for gitt distribusjonId (varselId i kafka eventen).
Det kan feks kafka problematikk som har gjort at bestilling av sms og epost videre til doknotifikasjon-2 ikke har skjedd, da kan de isf trigge bestilling på nytt.
Dersom det gjelder noe som allerde har blitt lest av bruker på min side kan distribusjonen patches til EKSPEDERT, og det vil ikke være nødvendig å sende noen varsler (dato_lest vil da isf være satt på journalposten). Det er mulig at det her ikke er noen innslag i doknotifikasjon-databasen dersom kafka-eventen ikke har blitt sendt av min-side.

## 6. Distribusjonsavvik DPO

Meldinger til trygderetten sendes nå via DPO. Om meldingen skal til trygderetten, se avsnitt 4.

## 7. Distribusjonavvik DPVT

Distribusjon til virksomheter som mottar meldinger i Altinn.
