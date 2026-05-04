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

---

## 1. Distribusjonsavvik PRINT

To verdikjeder distribuerer til sentral print:
1. **AFP-print fra Doksys** — batch via BMF001, BDOK002, BDIST005
2. **PDF-print fra Dokumentdistribusjon** — via QDIST008 og QDIST009

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| KLAR_FOR_DIST | KLAR_FOR_DIST | Feilet i QDIST009 / ligger på backoutkø. Forsøk rekjøring først. Sjekk logger. Ved vedvarende funksjonell feil: ta av kø, patch status til FEILET, meld fra til bestiller. |
| OVERSENDT | BEKREFTET | PDF-print: bekreftet mottatt men ikke kvittert EKSPEDERT. Etterlys status hos Skatteetaten — oppgi `dokumentId` (mailpieceId). Epost: Preprint@skatteetaten.no |
| BEKREFTET | OVERSENDT | AFP-print: bekreftet mottatt men ikke kvittert EKSPEDERT. Samme oppfølging som over. |
| OVERSENDT | OVERSENDT | Skatteetaten har ikke bekreftet mottak. Kjent problem, trolig filsluse. |
| OVERSENDT/BEKREFTET | EKSPEDERT | Happy case — printet, pakket og levert til posten. |

---

## 2. Distribusjonsavvik SDP/DPI

Distribusjon via Digdir til DigiPost/e-Boks. De fleste avvik skyldes forsinkede/manglende kvitteringer fra e-Boks.

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| KLAR_FOR_DIST | KLAR_FOR_DIST | Feilet i QDIST011, ligger på backoutkø `P_DOKDISTEFORMIDLING.QDIST011_DIST_TIL_DPI_BOQ`. Forsøk rekjøring. Ved vedvarende feil: ta av kø, patch til FEILET, meld til bestiller. |
| OVERSENDT | OVERSENDT | Sendt til Digdir men ingen bekreftelse innen frist. Etterlys status hos Digdir — oppgi `KONVERSASJON_ID`. Epost: servicedesk@digdir.no |
| EKSPEDERT | EKSPEDERT | Happy case — bekreftelse fra postkasseleverandør mottatt. |

---

## 3. Distribusjonsavvik E-HANDEL

Distribusjon til NETS av e-fakturaer fra OEBS, ELIN og PREDATOR. Avvik er sjeldne. Kvitteringer ankommer ofte noen timer etter rapportering — sjekk status manuelt før purring.

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| OVERSENDT | OVERSENDT | Sendt til NETS, men ingen bekreftelse innen frist. |
| FEILET | FEILET | Sjekk `feilkvittering.detaljer`. Typiske feil: "Receiver not found", "B2C issuer blocked", "Ugyldig forfallsdato". Teamet trenger **ikke** varsle — NETS varsler via "Daily forsendelsesrapport" og avvikene håndteres av OEBS/SITS. |
| BEKREFTET | EKSPEDERT | Happy case. |

Purring ved behov: payments-no@nets.eu

---

## 4. Distribusjonsavvik TRYGDERETTEN

Forsendelser behandles av QDIST013 via Altinn Meldingsformidler. Kvitteringer mottas normalt innen minutter (sdist001 sjekker hvert 10. minutt). DokdistAvstemming rapporterer etter 6 timer.

| Dist.status | Dok.status | Oppfølging |
|-------------|-----------|------------|
| KLAR_FOR_DIST | KLAR_FOR_DIST | Feilet i QDIST013, ligger på `P_DOKDISTEFORMIDLING.QDIST013_DIST_TRYGDE_BOQ`. Forsøk rekjøring. Ved vedvarende feil: ta av kø, patch til FEILET, meld til Klageinstans. |
| OVERSENDT | OVERSENDT | Sendt til Altinn men ikke bekreftet. Varsle Trygderetten og Klageinstans. Kan bety at integrasjonspunktet har stoppet. Ved rekjøring: patch status til KLAR_FOR_DIST, legg melding på kø til QDIST013. |
| BEKREFTET | BEKREFTET | Mottatt av integrasjonspunkt men ikke bekreftet av sak/arkiv-system. Varsle Trygderetten og Klageinstans. |
| EKSPEDERT | EKSPEDERT | Happy case. |

Se også: `trygderetten-kvitteringer.md` for detaljert oppfølging av manglende kvitteringer.
