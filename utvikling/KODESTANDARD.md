# Kodestandard

## Introduksjon

Dette dokumentet definerer Team Dokumentløsninger sin kodestandard for apper teamet er ansvarlig for.

Dokumentet beskriver hvordan koden skal se ut, hvordan den skal struktureres og hvilke prinsipper for utvikling teamet skal forholde seg til.

## Kildekodefiler

### Tegnsett: UTF-8

Kildekodefiler skal være i UTF-8. Dette gjelder både filer med kompilerbar kode og konfigurasjonsfiler.

**Merknad:**

Applikasjonene under kan hende kjører som latin1 (ISO-8859-1) og det kan sette annet krav til tegnsett:

* joark
* ondemandbrev
* dialoguedlf
* brevserver


## Kodeprinsipper

For å sørge for at kode vi skriver er vedlikeholbart i lang tid fremover så er det hensiktsmessig å ha noen
prinsipper om hvordan vi skriver kode slik at det er enkelt å forstå og teste.
På toppniva kan dette summeres med KISS(https://en.wikipedia.org/wiki/KISS_principle) og
POLA(https://en.wikipedia.org/wiki/Principle_of_least_astonishment)

### Immutability og pure functions

Det er ofte hensiktsmessig å skrive kode hvor tilstand ikke endres og funksjoner heller returerer nye
immutable objekter. Det man får ut av dette er kode som er idempotent og som ikke skaper eller påvirkes av 
sideeffekter. Gevinsten med dette er at man kan lese og skjønne kode uten å måtte ta hensyn til konteksten
rundt, fn(x) vil alltid returnere det samme uavhengig av konteksten rundt. Dette gjør det også mye enklere å
teste kode da vi ikke lenger er nødt til å mocke resten av universet.

> You wanted a banana but what you got was a gorilla holding the banana and the entire jungle.
> -Joe Armstrong

```javascript
function agePersonPure(person) {
    return new Person(person.name, person.age + 1);
}

const purePerson = new Person("Ola Normann", 50);
const slightlyOlderPurePerson = agePersonPure(purePerson);
const anotherSlightlyOlderPurePerson = agePersonPure(purePerson);

// purePerson: Person {name: "Ola Normann", age: 50}
// slightlyOlderPurePerson: Person {name: "Ola Normann", age: 51}
// anotherSlightlyOlderPurePerson: Person {name: "Ola Normann", age: 51}


function agePersonInpure(person) {
    person.age = person.age + 1;
}

let inpurePerson = new Person("Ola Normann", 50);
agePersonInpure(inpurePerson);
agePersonInpure(inpurePerson);

// inpurePerson: Person {name: "Ola Normann", age: 52}
```
I et leketøyeksempel som dette kan det virke uviktig,
men i en større kodebase blir du da nødt til å holde orden på når og hvor et objekt
blir mutert, samt hva du eventuelt påvirker når du muterer et objekt. Dette gjør det vanskligere 
å forstå kode, samtidig som det øker sjansen for å introdusere bugs og regresjoner.
