# Kontrollere distribusjon og varsel for Klageinstans

Rutine for kontroll av distribusjon og varsel. Klageinstans oppgir journalpostId til forsendelsen de ønsker informasjon om.

## 1. Hent informasjon om forsendelsen

```sql
alter session set current_schema = DOKUMENTDISTRIBUSJON;

select distInfo.DISTRIBUSJON_DATO, distInfo.K_DIST_STATUS, distInfo.K_DIST_KANAL,
       distinfo.k_distribusjonstype,
       dokInfo.DOKUMENT_ID, dokInfo.ARKIVKODE, dokInfo.MOTTAKER_ID,
       dokInfo.K_DOKUMENT_STATUS, dokInfo.EKSPEDERT_DATO, dokInfo.FORSENDELSE_TITTEL,
       dokRef.dokumenttype_id
from DOKUMENT_INFO dokinfo
  inner join DISTRIBUSJON_INFO distinfo on dokinfo.DISTRIBUSJON_INFO_ID = distinfo.DISTRIBUSJON_INFO_ID
  inner join dokument_referanse dokref on dokinfo.DOKUMENT_INFO_ID = dokref.DOKUMENT_INFO_ID
where dokinfo.ARKIVKODE = '<journalpostId>';
```

Gå videre basert på `K_DIST_KANAL`:
- `SDP` → seksjon 2
- `DITTNAV` → seksjon 3
- `DPVT` → seksjon 4

---

## 2. Distribusjonskanal = SDP (digital postkasse)

### 2.1 Finn varseltekst

#### Hvis DISTRIBUSJON_DATO er 20/5-2022 eller senere

Bruk `k_distribusjonstype` fra steg 1:

| k_distribusjonstype | Varseltekst |
|---------------------|-------------|
| VEDTAK | Du har fått et vedtak fra NAV. Les det i din digitale postkasse. |
| VIKTIG (eller null) | Du har fått et viktig brev fra NAV. Les det i din digitale postkasse. |
| ANNET | Du har fått et brev fra NAV. Les det i din digitale postkasse. |

#### Hvis DISTRIBUSJON_DATO er før 20/5-2022

Hent varseltekst fra dokkat-db:

```sql
alter session set current_schema = dokkat;

select di.dokumenttype_id, vm.k_kanal, vm.foerstegangsvarsel_tekst
from dokumenttype_info di
  inner join dokument_produksjon_info dpi on di.id = dpi.id
  inner join distribusjon_varsel dva on dpi.fk_distribusjon_info_id = dva.fk_distribusjon_info_id
  inner join varsel_info vi on dva.varseltype_id = vi.varseltype_id
  inner join varsel_mal vm on vi.id = vm.fk_varsel_info_id
where di.dokumenttype_id = '<dokumenttypeId>' and vi.k_varsel_for_dist_kanal = 'SDP';
```

### 2.2 Tilbakemelding til Klageinstans

#### Ferdig SQL for tilbakemelding (DISTRIBUSJON_DATO >= 20/5-2022)

```sql
select 'JournalpostId ' || t.journalpost_id || ' ble distribuert til digital postkasse ' || t.distribusjon_dato
|| ', og kvittering fra digital postkasse er mottatt ' || t.ekspedert_dato || '.' || chr(10) || chr(10) ||
'Vi vet ikke om mottaker har lest dokumentet i digital postkasse, kun at dokumentet er gjort tilgjengelig for mottaker.' || chr(10) ||
'Vi vet ikke om bruker har mottatt innbyggerstyrt varsel, da de kan ha skrudd av dette. Hvis innbyggerstyrt varsel var skrudd på for denne mottakeren, skal tittel "' || t.forsendelse_tittel || '" ha vært en del av varslingsteksten.' || chr(10) ||
'Mottaker skal ha mottatt avsenderstyrt varsel med teksten "'|| t.varseltekst || '". Hvis mottaker ikke har lest dokumentet innen 7 dager etter mottak, så skal de også ha mottatt et avsenderstyrt varsel med samme tekst.' as fagsystem_kommentar
from(
  select dokinfo.arkivkode as journalpost_id,
         to_char(distinfo.distribusjon_dato, 'DD.MM.YYYY HH24:MI:SS') as distribusjon_dato,
         to_char(dokinfo.ekspedert_dato, 'DD.MM.YYYY HH24:MI:SS') as ekspedert_dato,
         dokinfo.forsendelse_tittel as forsendelse_tittel,
         CASE k_distribusjonstype
           WHEN 'VEDTAK' THEN 'Du har fått et vedtak fra NAV. Les det i din digitale postkasse.'
           WHEN 'VIKTIG' THEN 'Du har fått et viktig brev fra NAV. Les det i din digitale postkasse.'
           WHEN 'ANNET' THEN 'Du har fått et brev fra NAV. Les det i din digitale postkasse.'
           ELSE 'Du har fått et viktig brev fra NAV. Les det i din digitale postkasse.'
         END AS varseltekst
  from DOKUMENT_INFO dokinfo
    inner join DISTRIBUSJON_INFO distinfo on dokinfo.distribusjon_info_id = distinfo.distribusjon_info_id
  where dokinfo.arkivkode = '<journalpostId>'
) t;
```

#### Svarmaler basert på distribusjonsdato

**Alle datoer (felles del):**
> JournalpostId `<journalpostId>` ble distribuert til digital postkasse `<DISTRIBUSJON_DATO>`, og kvittering fra digital postkasse er mottatt `<EKSPEDERT_DATO>`.
>
> Vi vet ikke om mottaker har lest dokumentet i digital postkasse, kun at dokumentet er gjort tilgjengelig for mottaker.
> Vi vet ikke om bruker har mottatt innbyggerstyrt varsel, da de kan ha skrudd av dette. Hvis innbyggerstyrt varsel var skrudd på for denne mottakeren, skal tittel «`<FORSENDELSE_TITTEL>`» ha vært en del av varslingsteksten.

**Tillegg for DISTRIBUSJON_DATO <= 25/10-2021:**
> Hvis mottaker ikke hadde lest dokumentet innen 7 dager etter mottak, så skal de ha mottatt et avsenderstyrt varsel med teksten «`<varseltekst>`».
> Digdir har ikke historikk på meldinger/varsel som er eldre enn 4 måneder.

**Tillegg for DISTRIBUSJON_DATO > 25/10-2021:**
> Mottaker skal ha mottatt avsenderstyrt varsel med teksten «`<varseltekst>`». Hvis mottaker ikke har lest dokumentet innen 7 dager etter mottak, så skal de også ha mottatt et avsenderstyrt varsel med samme tekst.

---

## 3. Distribusjonskanal = DITTNAV

### 3.1 Varsel sendt før 01.04.2022

#### Finn varseltypeId fra dokkat-db

```sql
alter session set current_schema = DOKKAT;

select di.dokumenttype_id, dva.varseltype_id
from dokumenttype_info di
  inner join dokument_produksjon_info dpi on di.id = dpi.id
  inner join distribusjon_varsel dva on dpi.fk_distribusjon_info_id = dva.fk_distribusjon_info_id
where di.dokumenttype_id = '<dokumenttypeId>' and dva.K_VARSEL_FOR_DIST_KANAL = 'DITT_NAV';
```

#### Finn varsel fra varsel-db

```sql
alter session set current_schema = VARSEL;

select vb.varselbestilling_id, vb.fnr, vb.varseltype_id, vb.endret_av, vb.endret_dato,
       va.k_kanal, va.sendt_tidspunkt, va.kontakt_info, va.varsel_tittel, va.varsel_tekst
from varselbestilling vb
  inner join varsel va on vb.id = va.fk_varselbestilling_id
where vb.varseltype_id = '<varseltype_id>'
  and vb.fnr = '<fnr>'
  and trunc(vb.opprettet_dato) = '<dato>';
```

#### Tilbakemelding

> JournalpostId `<journalpostId>` ble distribuert til DittNAV `<DISTRIBUSJON_DATO>`.
> Varselet (varselbestillingId `<varselbestilling_id>`) ble sendt til `<k_kanal>`.
> Epost-tittelen var «`<varsel_tittel der k_kanal=EPOST>`», og varselteksten var «`<varsel_tekst der k_kanal=EPOST>`».
> Sms-varselteksten var «`<varsel_tekst der k_kanal=SMS>`».
> DittNav-varselteksten (under «bjella») var «`<varsel_tekst der k_kanal=DITT_NAV>`».

Hvis `endret_av = "tvarsel004"`:
> Dokumentet ble åpnet av mottaker `<endret_dato>`.

Ellers:
> Vi har ikke informasjon om at bruker har lest dokumentet på nav.no / ditt nav.

### 3.2 Varsel sendt etter 01.04.2022

#### Finn varsel fra Doknotifikasjon-db

```sql
select noti.bestillings_id, noti.k_status, noti.opprettet_dato, noti.endret_av, noti.endret_dato,
       nodi.k_status, nodi.k_kanal, nodi.tittel, nodi.tekst, nodi.sendt_dato
from t_notifikasjon noti
  inner join t_notifikasjon_distribusjon nodi on noti.id = nodi.notifikasjon_id
where noti.bestillings_id like '<DOKUMENT_ID>';
```

#### Sjekk om dokumentet er lest

Vi kan utlede at dokumentet er lest dersom:
- `dato_lest` er satt i Joark, eller
- `endret_dato <> opprettet_dato` og `endret_dato <> opprettet_dato + 7 dager` i doknotifikasjon

```sql
alter session set current_schema = joark;

select CASE
  WHEN dato_lest IS NULL THEN 'Dato_lest er ikke satt'
  ELSE 'Dokumentet ble åpnet av mottaker ' || to_char(dato_lest, 'DD.MM.YYYY HH24:MI:SS') ||
       '. Journalpost posten er oppdatert med en dato i feltet dato_lest.'
END AS Varsel
FROM t_journalpost
where journalpost_id = '<journalpostId>';
```

---

## 4. Distribusjonskanal = DPVT (Altinn)

Dokumenter sendt gjennom DPVT er sendt til en norsk virksomhets innboks i Altinn via tjenesten "Taushetsbelagt Post fra NAV".

### Varslings- og påminnelsesflyt

1. Melding gjøres tilgjengelig i Altinn Innboks + sms/epost-varsel til varslingsadresse
2. Hvis ikke lest innen **3 dager** → påminnelse sendt til Altinn Innboks (via DPV) + sms/epost
3. Hvis ikke lest innen **7 dager** → sms/epost-påminnelse
4. Hvis påminnelse ikke lest innen **7 dager** (10 dager totalt) → sms/epost-påminnelse

### 4.1 Finn epost/sms varseltekst

```sql
select t.k_distribusjonstype, t.DISTRIBUSJON_DATO, t.varseltekst
from(
  select distinfo.k_distribusjonstype, distinfo.DISTRIBUSJON_DATO,
         dokInfo.MOTTAKER_ID, dokInfo.mottaker_navn, dokInfo.FORSENDELSE_TITTEL,
         case
           when distinfo.k_distribusjonstype = 'VEDTAK' then dokInfo.MOTTAKER_ID ||' '|| dokInfo.MOTTAKER_NAVN ||' har mottatt vedtaket «' || dokInfo.FORSENDELSE_TITTEL || '» fra NAV i Altinn. For å få tilgang til vedtaket må noen i '|| dokInfo.MOTTAKER_NAVN ||' få tilgang til tjenesten «Taushetsbelagt post fra NAV» i Altinn. Les mer om tildeling av tilganger og roller på Altinn."'
           when distinfo.k_distribusjonstype = 'VIKTIG' then dokInfo.MOTTAKER_ID ||' '|| dokInfo.MOTTAKER_NAVN ||' har mottatt viktig brev «' || dokInfo.FORSENDELSE_TITTEL || '» fra NAV i Altinn. For å få tilgang til brevet må noen i '|| dokInfo.MOTTAKER_NAVN ||' få tilgang til tjenesten «Taushetsbelagt post fra NAV» i Altinn. Les mer om tildeling av tilganger og roller på Altinn."'
           when distinfo.k_distribusjonstype is null then dokInfo.MOTTAKER_ID ||' '|| dokInfo.MOTTAKER_NAVN ||' har mottatt viktig brev «' || dokInfo.FORSENDELSE_TITTEL || '» fra NAV i Altinn. For å få tilgang til brevet må noen i '|| dokInfo.MOTTAKER_NAVN ||' få tilgang til tjenesten «Taushetsbelagt post fra NAV» i Altinn. Les mer om tildeling av tilganger og roller på Altinn."'
           when distinfo.k_distribusjonstype = 'ANNET' then dokInfo.MOTTAKER_ID ||' '|| dokInfo.MOTTAKER_NAVN ||' har mottatt meldingen «' || dokInfo.FORSENDELSE_TITTEL || '» fra NAV i Altinn. For å få tilgang til meldingen må noen i '|| dokInfo.MOTTAKER_NAVN ||' få tilgang til tjenesten «Taushetsbelagt post fra NAV» i Altinn. Les mer om tildeling av tilganger og roller på Altinn."'
           else 'noe gikk galt'
         end as varseltekst
  from DOKUMENT_INFO dokinfo
    inner join DISTRIBUSJON_INFO distinfo on dokinfo.DISTRIBUSJON_INFO_ID = distinfo.DISTRIBUSJON_INFO_ID
  where dokinfo.ARKIVKODE = '<journalpostId>'
) t;
```

### 4.2 Finn dato lest i Joark

SDIST007 oppdaterer Joark med `dato_lest` dersom dokumentet er lest innen 3 dager etter utsending.

```sql
select jp.journalpost_id, jp.dato_lest
from t_journalpost jp
where jp.journalpost_id = '<journalpostId>';
```

### 4.3 Tilbakemelding til Klageinstans

#### Hvis dato_lest er satt

> JournalpostId `<journalpostId>` ble distribuert til mottakers Altinn Innboks `<DISTRIBUSJON_DATO>`.
> sms/epost-varsel er bestilt gjennom Altinn med teksten `<varseltekst>`.
> Altinn har rapportert at meldingen lest av mottaker `<dato_lest>`.

#### Hvis dato_lest ikke er satt

> JournalpostId `<journalpostId>` ble distribuert til mottakers Altinn Innboks `<DISTRIBUSJON_DATO>`.
> sms/epost-varsel til mottakers varslingsadresse er bestilt gjennom Altinn, med teksten `<varseltekst>`. Hvis forsendelsen ikke er lest innen 7 dager sender Altinn sms/epost med påminnelse.
>
> Vi har ikke informasjon om når meldingen ble åpnet/lest.
>
> Mottaker kan selv se når meldingen ble mottatt, hvilke varsel som er sendt og hvem som har lest meldingen ved å gå inn i sin Altinn Innboks og se på historikken på meldingen. Ved behov kan Nav be om å få utlevert denne informasjonen ved å henvende seg til Altinn servicedesk.
