# QDIST011_FUNK_FEIL

Funksjonell feilkø for dokdisteformidling (DPI/SDP-distribusjon). Har **ikke** automatisk resending.

La meldingene ligge til neste dag før manuell analyse.

## Feilscenarioer

### 1. Manglende distribusjonsVarsel i DOKKAT

```
Tkat020FunctionalException: Fant ingen distribusjonVarsel med
varselForDistribusjonKanal=SDP for dokumenttypeId=U000001
```

Mangel i tabellen `DISTRIBUSJON_VARSEL` i DOKKAT-databasen. Verifiser med:

```sql
select * from DOKUMENTTYPE_INFO where DOKUMENTTYPE_ID = '<dokumenttypeId>';
```

### 2. Manglende sertifikat / kontaktinformasjon

```
IllegalKontaktInformasjonFunctionalException: Manglende sertifikat,
leverandoerAdresse eller brukerAdresse
```

**Tiltak:** Forsøk manuell resending via primærkø. Erfaringsmessig løser dette feilen.

### 3. Resending via nødprint

Gjelder meldinger som feiler med:
```
Bruker har reservert seg mot digitalkontaktinformasjon
```
eller:
```
Ingen kontaktinformasjon er registrert på personen
```

Denne meldingen skal egentlig ikke havne her, men når det skjer må resending via nødprint til.

#### Fremgangsmåte for nødprint

1. Finn forsendelsen — `forsendelseId = dokument_info_id` i dokdist-databasen
2. Opprett MMA-sak for å spore DB-endringene
3. Verifiser at `k_dist_status` og `k_dokument_status` er `KLAR_FOR_DIST` (patch hvis ikke)
4. Patch dokdist-databasen:

```sql
update distribusjon_info
set k_dist_kanal = 'PRINT',
    endret_av = 'MMA-XXXX',
    endret_dato = systimestamp
where distribusjon_info_id = '<distribusjon_info_id>';

update dokument_referanse
set dokumenttype_id = 'U000001',
    endret_av = 'MMA-XXXX',
    endret_dato = systimestamp
where dokument_info_id = '<dokument_info_id>';
```

5. Legg melding på kø til qdist009 (bestill via Atom-sak)
6. Fjern meldingen fra feilkø
7. Verifiser at status endres til `OVERSENDT` i dokdist-databasen
