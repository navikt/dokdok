Hvis en melding sendt til DPI men vi ikke fått ekspedert / feilet-kvittering. Kontaktet DigDir og de sier meldingen feilet og sende på nytt:

- databasepatch i dokumentdistribusjon sette `dokument_info.konversasjon_id` til null (status er `OVERSENDT` eller `KLAR_TIL_DIST` funker begge tilfeller)
- legge melding på qdist011: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><ns2:distribuerTilKanal xmlns:ns2="http://nav.no/melding/virksomhet/dokdistfordeling"><forsendelseId>[dokument_info_id i dokumentdistribusjon-databasen]</forsendelseId></ns2:distribuerTilKanal>`
