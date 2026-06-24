# Skanningavvik

Håndtering av feil i skanning-mottak fra Iron Mountain og avviksrapportering.

## Bakgrunn

Fra tid til annen feiler overføringen av filer fra Iron Mountain til Nav. Bjoark003 gjør avstemming og oppretter IKT-saker ved avvik. Typisk sak:

```
Filer lest:
/was_app/batch/joark/bjoark003/input_SKANMOTOVRIG_AVSTEMMING/17.11.2022_Avstemmingsfil_NAVFAGPOST.txt
Antall filer avstemt: 246
Antall filer funnet: 245
Antall filer feilet: 1
Filer som ikke ble funnet:
OVRIG_16.11.2022_R511796699_4_1284.pdf
```

## Fremgangsmåte

### Finn ut hva som gikk galt

Alle skanmot-apper er funksjonelt like — fremgangsmåten gjelder for alle.

**Søk i loggene** etter filnavnet (uten .pdf), en dag eller to før datoen i filnavnet:

```
OVRIG_16.11.2022_R511796699_4_1284
```

#### Funksjonell feil i skanmot

Hvis du finner logginnslag av denne typen, hopp til steg 3 (kontakt Iron Mountain):

```
Skanmotovrig feilet funksjonelt for fil=OVRIG_16.11.2022_R511796699_4_1284,
batch=16.11.2022_R511796699_4_576126.
SkanningmetadataValidationException: Kunne ikke unmarshalle xml:
SAXParseException: cvc-pattern-valid: Value '' is not facet-valid with
respect to pattern '[0-9]{9,11}' for type 'brukerIdType'.
```

#### Fil ikke overført

Hvis ingen logginnslag → dobbeltsjekk i Joark:

```sql
SELECT *
FROM t_journalpost j
WHERE j.kanal_referanse_id in ('<filnavn>.pdf');
```

Ingen treff = filen er ikke mottatt.

### 3. Kontakt Iron Mountain

Send epost:

**Til:** Iron Mountain-kontakt (spør på Slack for e-postadresse)
**Kopi:** teamdokumenthandtering-epost

#### Epost-mal: Manglende filer

```
Emne: Nav - manglende filer i avstemmingsfil SKANMOT<app> datert <dd.mm>

Hei

Nav savner avstemmingsfilen under:

Filer lest:
<filsti fra IKT-saken>
Antall filer avstemt: <antall>
Antall filer funnet: <antall>
Antall filer feilet: <antall>
Filer som ikke ble funnet:
<liste over filnavn>
```

#### Epost-mal: Manglende avstemmingsfiler

```
Emne: Nav savner avstemmingsfiler for <områder> <dd.mm>

Hei Iron Mountain

Nav savner avstemmingsfiler for områdene <SKANMOTREFERANSENR/SKANMOTUTGAAENDE/etc> for den <dd.mm>.
Kan dere også kvalitetssikre at de inneholder riktig data før de sendes over på nytt.
```

#### Epost-mal: Feil metadata

```
Emne: Nav savner filer fra <SKANMOT-app> <dd.mm>

Hei Iron Mountain

Nav savner filer som feilet under avstemming den <dd.mm>.

Antall filer avstemt: <antall>
Antall filer funnet: <antall>
Antall filer feilet: <antall>
Filer som ikke ble funnet:
<filnavn> - savnes
<filnavn> - har feil metadata i .xml. <beskrivelse av feil>
```
