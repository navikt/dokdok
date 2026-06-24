# Rutiner for Dokumentvakten

Oppgaver som skal utføres daglig av rollen dokvakt i Team Dokumentløsninger.
Ansvaret går på omgang mellom utviklerne. Hver mandag gjøres overlevering på backlog-møtet.

## Hovedoppgaver

1. Håndtere MQ-avvik
2. Slack-henvendelser til teamet eller advarsler fra apper
3. Undersøke feil på periodiske jobber
4. Se på skanningavvik og distribusjonsavvik rapportert i Jira

## 1. Håndtere MQ-avvik fra backoutboardet

Overvåk MQ-meldinger som havner på tekniske og funksjonelle feilkøer. Status vises i Grafana-boardet for Dokumentvakten.

### Tekniske feilkøer

- Har automatisk resending kl 7, 9, 11, 13, 15, 17, 19, 21 (mandag–fredag)
- Resendinger dokumenteres på #dok_bq_resendinger
- Normalt **ikke** nødvendig å håndtere manuelt
- Dersom meldinger etter autoresending havner på feilkø igjen → undersøk nærmere

### Funksjonelle feilkøer

- Krever **manuell analyse**
- Start med loggsøk på callId eller bestillingsId fra meldingen
- Hvis forbigående teknisk feil → resending via MQ-verktøyet
- Hvis ikke → videre analyse, eventuelt DB-patching, deretter resending

## 2. Følge med i Slack-kanaler

Dokumentvakten har ansvar for å følge med og respondere på henvendelser i:

| Kanal | Formål |
|-------|--------|
| #team_dokumentløsninger | Hovedkanal — henvendelser til teamet |
| #dokhendelser | Rapporter fra appene — svar ut feilmeldinger |
| #dokmorgenvakt | Historikk — søk etter lignende problemer som er løst før |
| #produksjonshendelser | Hendelser på tvers av team |

Hele teamet har kollektivt ansvar for å bidra i disse kanalene.

## 3. Undersøke feil på periodiske jobber

Periodiske jobber varsler via Slack dersom de feiler. Undersøk logger (Grafana/Loki e.l.).

Tekniske/funksjonelle feil for skanmot-appene blir også varslet om via Slack:
- `feil-i-skanning.md`

### Jobber som overvåkes

| Applikasjon | Jobb | Beskrivelse |
|-------------|------|-------------|
| Doksikkerhetsnett | OppdaterMetrikker | Lager Grafana-metrikker for journalposter uten oppgave |
| Doksikkerhetsnett | OpprettOppgaver | Lager oppgaver for glemte inngående journalposter |
| Dokdistavstemming | Sdist002 | Oppretter Jira-oppgaver |
| Dokdistavstemming | Sdist004 | Oppdater journalposter med ekspedertstatus og utsendingsinfo |
| Dokdistavstemming | Sdist006 | Sender uåpnede nav.no-sendinger til sentral print |
| Dokdistdpi-2 | Sdist003 | Henter kvitteringer på DPI-bestillinger |
| Dokdistdpi-2 | Sdist005 | Henter status på forsendelser som mangler kvittering |
| Doknotifikasjon-2 | Snot001 | Rebestiller distribusjon av notifikasjoner |
| Doknotifikasjon-2 | Snot002 | Ferdigstiller notifikasjoner og publiserer statusendring |
| Skanmot-apper | Skanmotreferansenr, skanmothelse, skanmotovrig, skanmotutgaaende | Leser inn PGP-krypterte filer fra Iron Mountain |

## 4. Se på skanningavvik og distribusjonsavvik

Jira-oppgaver opprettes for:
- **Skanningavvik** — feil ved innlesing av skannet post fra Iron Mountain
- **Distribusjonsavvik** — forsendelser som ikke er kvittert innen frist

Disse bør ikke bli liggende for lenge. Dokumentvakten har ansvar for å følge opp.

Se egne HOWTOs:
- `skanningavvik.md`
- `distribusjonsavvik.md`
