# Trygderetten-kvitteringer

Oppfølging av manglende kvitteringer fra Trygderetten.

## Bakgrunn

Distribusjon til Trygderetten skjer gjennom dokdisteformidling. Noen ganger mottas ikke kvitteringer — erfaringsmessig skyldes dette at mottaket hos Trygderetten har feilet.

## Undersøk status

Sjekk forsendelsene i dokumentdistribusjon-databasen:

```sql
select distribusjon_dato, arkivkode, di.dokument_id, k_dokument_status
from distribusjon_info d
join dokument_info di on d.distribusjon_info_id = di.distribusjon_info_id
where dokument_id in ('<dokumentId>');
```

- `OVERSENDT` = NAV har ikke fått kvittering
- `EKSPEDERT` = kvittering mottatt OK

## Håndtering

### Hvis status er OVERSENDT (og det har gått flere timer)

Send epost til Trygderetten og Klageinstans med teamet på kopi:

- **Trygderetten:** E-post til trygderetten (sjekk med teamet for riktig adresse)
- **Klageinstans:** E-post til klageinstans (sjekk med teamet for riktig adresse)
- **Kopi:** teamdokumenthandtering-epost

Merk: vi har også en slack-kanal for kommunikasjon.

#### Epost-mal

```
Emne: NAV savner kvitteringer fra Trygderetten

Hei

NAV savner kvitteringer for forsendelser sendt til dere mellom <dd.mm> og <dd.mm>.
Kan dere undersøke hva som har skjedd? Ber om at dere svarer alle mottakere av eposten,
også de på kopi.

Det gjelder disse forsendelsene:

| distribusjondato | journalpostId | dokumentId |
| <dato> | <journalpostId> | <dokumentId> |
```

Etter avklaring: send liste med alle dokumentId og **få bekreftet fra Trygderetten at sakene er mottatt OK**. Dokumenter dette i MMA-saken.

### Hvis status er EKSPEDERT på alle

Sannsynligvis forsinkede kvitteringer. Dokumenter funn på saken — den kan lukkes.

---

## VIKTIG: Ingen manuelle patcher av status

> **Det er IKKE tillatt å manuelt patche status til EKSPEDERT.**
> Det er dokdisteformidling som skal sette til EKSPEDERT med maskinelle kvitteringer fra eFormidling.
>
> Vi **MÅ** få bekreftet at alle sakene er overført Trygderetten og mottatt OK før MMA-saken lukkes.
>
> Grunnen: Hvis saker ikke er mottatt av Trygderetten kan det ikke bli oppdaget før lang tid etter,
> noe som går ut over bruker og kan skape negative konsekvenser for NAV juridisk.
