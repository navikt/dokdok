# QOPP001_FUNK_FEIL

Funksjonell feilkø for dokopp (oppgaveopprettelse). Har **ikke** automatisk resending.

## Fremgangsmåte

Finn journalpostId i feltet `<arkivkode>` i meldingen, og søk etter feilmeldingen i loggene til dokopp.

## Feilscenarioer

### 1. RETUR med Maskinell enhet 9999

```
Kan ikke opprette oppgave for RETUR for melding med Maskinell enhet=9999
```

Ingen håndtering for returpost fra maskinell enhet.

**Tiltak:** Flytt til `P_TRASH`.

### 2. RETUR med fagområde GEN

```
Kan ikke opprette oppgave for RETUR for melding med fagområde=GEN
```

Ingen ansvarlig for returpost fra utlandet.

**Tiltak:** Flytt til `P_TRASH`.

### 3. Oppgavetype RETUR ikke gyldig for tema

```
Oppgavetype: RETUR er ikke gyldig for tema: XXX
```

Skjer f.eks. for nye temaer der håndtering av retur ikke er avklart.

**Tiltak:** Hør med oppgavebehandling-teamet, eventuelt en arkitekt på teamet.

### 4. BrevdataValideringFeiletException for DokumentTypeId 000120

Skjer regelmessig.

**Tiltak:** Hent ut bestillingsId og journalsakId (fagsakNr hos pensjon), og meld til Team Pensjonbrev via #po-pensjon-teampensjonsbrev.

### 5. Fant ingen journalpost

```
Fant ingen journalpost med journalpostId=XXXX
```

Journalposter kan ha blitt slettet.

**Tiltak:** Undersøk lenger tilbake i loggene for å se om journalposten er slettet. Dersom journalposten er slettet kan meldingen også slettes.
