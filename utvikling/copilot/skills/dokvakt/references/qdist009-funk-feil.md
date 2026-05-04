# QDIST009_FUNK_FEIL

Funksjonell feilkø for dokdistsentralprint. Har **ikke** automatisk resending.

La meldingene ligge til neste dag før manuell analyse.

## Feilscenarioer

### 1. GetPostDestinasjon 403 FORBIDDEN

```
Rdist001GetPostDestinasjonFunctionalException: Kall mot rdist001 - GetPostDestinasjon feilet
funksjonelt med statusKode=403 FORBIDDEN, feilmelding=403 Forbidden: [no body]
```

**Tiltak:** Legg meldingen tilbake på originalkø. Trolig forbigående feil.

### 2. TREG002 — person død eller utflyttet

```
HttpStatusKode=410 GONE ... "Person er død og har ingen registrerte kontaktsopplysninger for dødsbo"
```
eller:
```
HttpStatusKode=404 NOT_FOUND ... "Fant ikke adresse for personen i PDL, med status=utflyttet
og kilde=folkeregistermyndigheten"
```

**Tiltak:** Flytt til trash. Sjekk om meldingene henger sammen med SDIST006 (uåpnede sendinger til sentral print) ved å søke i loggene. I så fall kan de slettes uten videre.
