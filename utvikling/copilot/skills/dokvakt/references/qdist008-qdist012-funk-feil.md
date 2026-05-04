# QDIST008/QDIST012_FUNK_FEIL

Funksjonelle feilkøer for dokdistfordeling. Har **ikke** automatisk resending.

La meldingene ligge til neste dag før manuell analyse.

## Feilscenarioer

### 1. Validation failed — feil i adressefelt

```
SchemaValidationException: Validation failed ...
Invalid content was found starting with element 'land'.
One of '{adresselinje3, postnummer}' is expected.
```

Adresselinjene er plassert i feil felter i dokprod-databasen.

#### 1a) Verifiser postadresse i dokprod

Finn journalpost-id i feltet `arkivkode` i meldingen.

```sql
select f.forsendelse_id, f.opprettet_dato, p.*
from forsendelse f
join DOKPROD.forsendelse_info fi on fi.forsendelse_info_id = f.forsendelse_info_id
left join postadresse p on fi.postadresse_id = p.postadresse_id
where journalpost_id = <journalpostId>;
```

Undersøk postadresse-tabellen for å finne feilplasserte felter (f.eks. postnummer plassert i adresselinje2).

#### 1b) Patch postadresse og forsendelse-status

Opprett IKT-sak for databasepatching. Eksempel:

```sql
update postadresse set
  ADRESSELINJE2 = '',
  POSTNUMMER = '<postnummer>',
  POSTSTED = '<poststed>',
  ENDRET_DATO = systimestamp,
  ENDRET_AV = 'MMA-XXXX'
where POSTADRESSE_ID = <postadresseId>;

update forsendelse set
  K_FORSENDELSE_STATUS = 'PRODUSERT',
  ENDRET_DATO = systimestamp,
  ENDRET_AV = 'MMA-XXXX'
where forsendelse_id = '<forsendelseId>';
```

#### 1c) Bestill ny distribusjon via QDOK107

Legg en melding på `P_DOKPROD.QDOK107.BESTILL_DISTRIBUSJON`:

```xml
<ns2:DistribuerForsendelse xmlns:ns2="http://dok.nav.no/dokprod/qdok102">
  <forsendelseId>12345678</forsendelseId>
  <produksjonsdato>2020-02-10T12:00:00.000</produksjonsdato>
</ns2:DistribuerForsendelse>
```

Flytt meldingen på feilkø til `P_TRASH`.

#### 1d) Hvis adressefeltene er uleselige

Sjekk selve brevet i Joark:

```sql
SELECT *
FROM t_journalpost j
  JOIN t_jp_dok_info_rel r ON j.journalpost_id = r.journalpost_id
  JOIN t_dokument_info tdi ON tdi.DOKUMENT_INFO_ID = r.DOKUMENT_INFO_ID
  JOIN t_fil_detaljer tfd ON tdi.dokument_info_id = tfd.dokument_info_id
  JOIN t_dokument_fil d ON d.fil_uuid = tfd.fil_uuid
WHERE j.JOURNALPOST_ID = <journalpostId>;
```

### 2. SafJournalpostIkkeFunnetFunctionalException

Ofte finnes journalpostene likevel i Joark. Trolig en forbigående feil som burde vært klassifisert som teknisk.

**Tiltak:** Forsøk resending først.

### 3. Avvist av SAF tilgangskontroll

```
SafHentDokumentFunctionalException: Kall mot saf:hentdokument feilet funksjonelt
med statusKode=403 FORBIDDEN ... "Avvist av SAF tilgangskontroll"
```

**Tiltak:** Forsøk resending.

### 4. Validation failed — Bruker=null

```
ValidationException: For journalposter kan feltet ...SafJournalpostTo.Bruker
ikke være null eller tomt. Fikk ...Bruker=null
```

**Tiltak:** Forsøk resending. Erfaringsmessig går disse gjennom ved resending.

### 5. Invalid content — land i stedet for adresselinje1

```
Invalid content was found starting with element 'land'.
One of '{adresselinje1}' is expected.
```

Mangel i adressedata. Krever manuell korrigering:

1. Dekrypter body i meldingen med `CryptoTest`-klassen i dokdistfordeling-prosjektet
2. Finn riktig adresse (fra Joark-dokument eller PDL-web)
3. Editer XML-en med korrekte adressedata
4. Krypter den editerte XML-en
5. Unload meldingen fra feilkø til fil
6. Erstatt kryptert innhold med ny versjon
7. Load meldingen tilbake på `P_DOKDISTFORDELING.QDIST012_HENT_DOK_JOARK`
8. Verifiser i loggene at alt gikk OK

### 6. Ugyldig status EKSPEDERT

```
ugyldig status=EKSPEDERT og distribusjon av bestillingsId=<bestillingsId> avbrytes
```

Bestillingen ble persistert på køen men fagsystemet fikk feil tilbake, og la inn en ny bestilling.

**Tiltak:**
1. Undersøk logger — finnes en ny bestilling for samme journalpost fra samme fagsystem?
2. Hvis ja → flytt den feilende bestillingen til `P_TRASH`
